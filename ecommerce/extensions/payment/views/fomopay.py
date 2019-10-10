"""FOMO Pay payment processing views."""

import base64
import logging
import StringIO

import qrcode
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from oscar.apps.partner import strategy
from oscar.apps.payment.exceptions import PaymentError, TransactionDeclined, UserCancelled
from oscar.core.loading import get_class, get_model
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ecommerce.edunext.conf import settings
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.exceptions import (
    AuthorizationError,
    DuplicateReferenceNumber,
    InvalidBasketError,
    InvalidSignatureError
)
from ecommerce.extensions.payment.processors.fomopay import Fomopay

logger = logging.getLogger(__name__)

Applicator = get_class('offer.applicator', 'Applicator')
Basket = get_model('basket', 'Basket')
BillingAddress = get_model('order', 'BillingAddress')
Country = get_model('address', 'Country')
Order = get_model('order', 'Order')
OrderNumberGenerator = get_class('order.utils', 'OrderNumberGenerator')
OrderTotalCalculator = get_class('checkout.calculators', 'OrderTotalCalculator')
NoShippingRequired = get_class('shipping.methods', 'NoShippingRequired')


class FomopayQRView(LoginRequiredMixin, View):
    """Starts FOMO Pay payment process.

    This view acts as an interface between the user and FOMO Pay,
    it'll mainly display the QR code and instructions on how to make a payment with the WeChat app.
    """
    # PermissionDenied exception will be raised instead of the redirect to login.
    raise_exception = True

    def __init__(self):
        super(FomopayQRView, self).__init__()
        site_settings = settings.get_current_request_site_options()
        self.debug = True if site_settings.get('FOMOPAY_DEBUG') == 'True' else False

    # Disable CSRF validation. The internal POST requests to render this view
    # don't include the CSRF token as hosted-side payment processor are
    # excepted to be externally hosted, but this is not the case.
    # Instead of changing the checkout flow for all the payment processors
    # this view is marked as exempt.
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(FomopayQRView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        """Render QR Code.

        Process the incoming request to render the QR in the template.
        """
        try:
            qr_url = self._get_qr_link(request)
            qr_img = self._generate_qr(qr_url)
            order_id = FomopayPaymentResponseView.get_transaction_id(request=request)
            status_url = reverse('fomopay:status')

            context = {
                'qrcode': qr_img,
                'order_id': order_id,
                'status_url': status_url,
                'receipt_page': self._get_receipt_page(order_id),
                'error_page': reverse('payment_error'),
            }

            return render(request, 'payment/fomopay.html', context)
        except Exception as err:  # pylint: disable=broad-except
            logger.error('FOMO Pay QR Code failed with error [%s]', str(err))
            return redirect(reverse('payment_error'))

    def _generate_qr(self, qr_url):
        """
        Create a base64 representation of the QR code image.
        """
        img = qrcode.make(qr_url)
        img_io = StringIO.StringIO()
        img.save(img_io, format='PNG')

        return base64.b64encode(img_io.getvalue())

    def _get_qr_link(self, request):
        """
        Process the outgoing request to the FOMO API to obtain the
        link needed to create the QR code
        """
        params = request.POST.dict()
        api_url = params.pop('api_url')
        response = requests.post(url=api_url, data=params)
        fomo_response = response.json()
        qr_url = fomo_response.get('url')

        if self.debug:
            logger.info('Outgoing FOMO Pay QR Code POST request with data: [%s],'
                        'FOMO Pay response: [%s]',
                        request.POST.dict(),
                        response.content)

        if not qr_url:
            logger.error('FOMO Pay QR Code generation failed for request[%s].'
                         'with FOMO Pay response [%s]',
                         request.POST.dict(),
                         response.content)

            raise PaymentError

        return qr_url

    def _get_receipt_page(self, order_id):
        """ Get receipt page for given order."""
        receipt_page_url = get_receipt_page_url(
            self.request.site.siteconfiguration,
            order_number=order_id
        )

        return receipt_page_url


class IsBasketOwner(BasePermission):
    """
    Global permission to only allow owners of an order/basket to poll it.
    """
    def has_permission(self, request, view):
        try:
            order_number = request.query_params.get('order_id')
            basket_id = OrderNumberGenerator().basket_id(order_number)
            basket = Basket.objects.get(id=basket_id)
            user = request.user
            return basket.owner == user
        except:  # pylint: disable=bare-except
            return False


class FomopayPaymentStatusView(APIView):
    """Polls payment status.

    Return the current status of the payment by polling the order
    or the basket status.
    """
    permission_classes = [IsAuthenticated, IsBasketOwner]

    def __init__(self):
        super(FomopayPaymentStatusView, self).__init__()
        site_settings = settings.get_current_request_site_options()
        self.debug = True if site_settings.get('FOMOPAY_DEBUG') == 'True' else False

    def get(self, request):
        """Provide confirmation of payment."""
        if self.debug:
            logger.info(
                'Incoming FOMO Pay Payment status poll GET request with data: [%s]',
                request.query_params,
            )
        status = self._get_payment_status(request)
        content = {
            'status': status
        }

        if self.debug:
            logger.info(
                'Incoming FOMO Pay Payment status poll GET request with data: [%s],'
                'response: [%s]',
                request.query_params,
                content,
            )

        return Response(content)

    def _get_payment_status(self, request):
        """Get the current state of the payment."""
        order_number = request.query_params.get('order_id')

        try:
            order = Order.objects.get(number=order_number)

            if order.status == 'Complete':
                return 'success'

        except:  # pylint: disable=bare-except
            logger.info(
                'Polling WeChat Payment: No payment found for order [%s] ',
                order_number,
            )

        try:
            basket_id = OrderNumberGenerator().basket_id(order_number)
            basket = Basket.objects.get(id=basket_id)

            if basket.status == 'CLOSED':
                logger.info(
                    'Polling WeChat Payment: Basket closed for order [%s] ',
                    order_number,
                )
                return 'error'
        except:  # pylint: disable=bare-except
            return 'in progress'


class FomopayPaymentResponseView(EdxOrderPlacementMixin, APIView):
    """ Starts FOMO Pay payment process.

    This view is intended to be called asynchronously by the payment processor.
    The view expects POST data containing a transaction ID and the payment result
    to complete the fulfillment pipeline.
    """

    def __init__(self):
        super(FomopayPaymentResponseView, self).__init__()
        site_settings = settings.get_current_request_site_options()
        self.debug = True if site_settings.get('FOMOPAY_DEBUG') == 'True' else False

    # Disable atomicity for the view. Otherwise, we'd be unable to commit to the database
    # until the request had concluded; Django will refuse to commit when an atomic() block
    # is active, since that would break atomicity. Without an order present in the database
    # at the time fulfillment is attempted, asynchronous order fulfillment tasks will fail.
    @method_decorator(transaction.non_atomic_requests)
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(FomopayPaymentResponseView, self).dispatch(request, *args, **kwargs)

    @property
    def payment_processor(self):
        return Fomopay(self.request.site)

    def post(self, request):
        """
        Process a FOMO Pay merchant notification and place an order for paid products as appropriate.
        """
        if self.debug:
            logger.info(
                'Incoming FOMO Pay Payment notification POST request with data: [%s]',
                request.POST.dict(),
            )

        try:
            notification = request.POST.dict()
            basket = self.validate_notification(notification)
        except:  # pylint: disable=bare-except
            self._close_basket(request)
            return Response(status=200)

        try:
            order = self.create_order(request, basket, self._get_billing_address(basket))
            self.handle_post_order(order)

            if self.debug:
                logger.info(
                    'Incoming FOMO Pay Payment notification POST request with data: [%s]'
                    'result: ORDER PLACED',
                    request.POST.dict()
                )

            return Response(status=200)
        except Exception as err:  # pylint: disable=broad-except
            self._close_basket(request)

            if self.debug:
                logger.info(
                    'Incoming FOMO Pay Payment notification POST request with data: [%s],'
                    'result: BASKET CLOSED, the placement process failed'
                    'error: [%s]',
                    request.POST.dict(),
                    str(err)
                )
            return Response(status=200)

    @staticmethod
    def get_transaction_id(request=None, notification=None):
        """Obtain the transaction id by removing the nonce."""
        if request:
            params = request.POST.dict()
        elif notification:
            params = notification

        if '$' in params.get('transaction'):
            return params['transaction'].split('$')[1]

        raise InvalidBasketError

    def _close_basket(self, request):
        """
        Change status of basket to CLOSED to indicate there was an error
        when processing the payment.
        """
        order_number = self.get_transaction_id(request=request)
        basket_id = OrderNumberGenerator().basket_id(order_number)
        basket = Basket.objects.get(id=basket_id)
        basket.status = 'CLOSED'
        basket.save()

    def validate_notification(self, notification):
        """
        Process the incoming notification to verify origin's authenticity and transaction result.
        """
        # Note (CCB): Orders should not be created until the payment processor has validated the response's signature.
        # This validation is performed in the handle_payment method. After that method succeeds, the response can be
        # safely assumed to have originated from FOMO Pay.
        basket = None
        transaction_id = None

        try:
            # The transaction id refers to the ID generated by FOMO Pay
            transaction_id = notification.get('payment_id')
            # FOMO Pay uses the transaction field as the reference code or order number
            order_number = self.get_transaction_id(notification=notification)
            basket_id = OrderNumberGenerator().basket_id(order_number)

            logger.info(
                'Received FOMO Pay payment notification for payment id [%s], associated with basket [%d].',
                transaction_id,
                basket_id
            )

            basket = self._get_basket(basket_id)

            if not basket:
                logger.error('Received FOMO Pay payment notification for non-existent basket [%s].', basket_id)
                raise InvalidBasketError

            if basket.status != Basket.FROZEN:
                # We don't know how serious this situation is at this point, hence
                # the INFO level logging. This notification is most likely FOMO Pay
                # telling us that they've declined an attempt to pay for an existing order.
                logger.info(
                    'Received FOMO Pay payment notification for basket [%d] which is in a non-frozen state, [%s]',
                    basket.id, basket.status
                )
        finally:
            # Store the response in the database regardless of its authenticity.
            ppr = self.payment_processor.record_processor_response(
                notification, transaction_id=transaction_id, basket=basket
            )

        # Explicitly delimit operations which will be rolled back if an exception occurs.
        with transaction.atomic():
            try:
                self.handle_payment(notification, basket)
            except InvalidSignatureError:
                logger.exception(
                    'Received an invalid signature in the FOMO Pay response for basket [%d] .'
                    'The payment response was recorded in entry [%d].',
                    basket.id,
                    ppr.id
                )
                raise
            except (UserCancelled, TransactionDeclined) as exception:
                logger.info(
                    'FOMO Pay payment did not complete for basket [%d] because [%s]. '
                    'The payment response [%s] was recorded in entry [%d].',
                    basket.id,
                    exception.__class__.__name__,
                    notification.get("result", "Unknown Error"),
                    ppr.id
                )
                raise
            except DuplicateReferenceNumber:
                logger.info(
                    'Received FOMO Pay payment notification for basket [%d] which is associated '
                    'with existing order [%s]. No payment was collected, and no new order will be created.',
                    basket.id,
                    order_number
                )
                raise
            except AuthorizationError:
                logger.info(
                    'Payment Authorization was declined for basket [%d]. The payment response was '
                    'recorded in entry [%d].',
                    basket.id,
                    ppr.id,
                )
            except PaymentError:
                logger.exception(
                    'FOMO Pay payment failed for basket [%d]. The payment response [%s] was recorded in entry [%d].',
                    basket.id,
                    notification.get("result", "Unknown Error"),
                    ppr.id
                )
                raise
            except:  # pylint: disable=bare-except
                logger.exception(
                    'Attempts to handle payment for basket [%d] failed. The payment response [%s] was recorded in'
                    ' entry [%d].',
                    basket.id,
                    notification.get("result", "Unknown Error"),
                    ppr.id
                )
                raise

        return basket

    def _get_basket(self, basket_id):
        """Return basket object from the basket_id."""
        if not basket_id:
            return None

        try:
            basket_id = int(basket_id)
            basket = Basket.objects.get(id=basket_id)
            basket.strategy = strategy.Default()
            Applicator().apply(basket, basket.owner, self.request)
            return basket
        except (ValueError, ObjectDoesNotExist):
            return None

    def create_order(self, request, basket, billing_address):
        """Place the order and begin fulfillment pipeline."""
        order_number = OrderNumberGenerator().order_number(basket)
        try:
            shipping_method = NoShippingRequired()
            shipping_charge = shipping_method.calculate(basket)

            # Note (CCB): This calculation assumes the payment processor has not sent a partial authorization,
            # thus we use the amounts stored in the database rather than those received from the payment processor.
            order_total = OrderTotalCalculator().calculate(basket, shipping_charge)
            user = basket.owner

            return self.handle_order_placement(
                order_number,
                user,
                basket,
                None,
                shipping_method,
                shipping_charge,
                billing_address,
                order_total,
                request=request
            )
        except Exception:  # pylint: disable=broad-except
            self.log_order_placement_exception(order_number, basket.id)
            raise

    def _get_billing_address(self, basket):
        """ Fill in the billing address using the payment notification.

        FOMO Pay doesn't provide a billing address in the payment notification,
        so as a temporal address we're storing the basket owner information.
        """
        return BillingAddress(
            first_name=basket.owner.full_name,
            last_name='',
            line1=basket.owner.email,
            line4='',
            country=Country.objects.get(
                iso_3166_1_a2='SG'))
