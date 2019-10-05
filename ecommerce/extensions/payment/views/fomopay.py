"""FOMO Pay payment processing views."""

import base64
import logging
import StringIO

import qrcode
import requests
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from oscar.apps.partner import strategy
from oscar.apps.payment.exceptions import PaymentError, TransactionDeclined, UserCancelled
from oscar.core.loading import get_class, get_model
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

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


class FomopayQRView(View):
    """Starts FOMO Pay payment process.

    This view acts as an interface between the user and FOMO Pay,
    it'll mainly display the QR code and instructions on how to make a payment with the WeChat app.
    """

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
        qr_url = self._get_qr_link(request)
        qr_img = self._generate_qr(qr_url)
        order_id = request.POST.get('transaction')
        status_url = reverse('fomopay:status')
        context = {
            'qrcode': qr_img,
            'order_id': order_id,
            'status_url': status_url,
            'receipt_page': self._get_receipt_page(order_id)}

        return render(request, 'payment/fomopay.html', context)

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

        return qr_url

    def _get_receipt_page(self, order_id):
        """ Get receipt page for given order."""
        receipt_page_url = get_receipt_page_url(
            self.request.site.siteconfiguration,
            order_number=order_id
        )

        return receipt_page_url

class FomopayPaymentStatusView(APIView):
    # TODO: implement security to prevent unauthorized access.
    # permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """Provide confirmation of payment."""
        status = self._get_payment_status(request)
        content = {
            'status': status
        }

        return Response(content)

    def _get_payment_status(self, request):
        """Get the current state of the payment."""
        order_number = request.query_params.get('order_id')

        try:
            order = Order.objects.get(number=order_number)
            status = 'success' if order.status == 'Complete' else 'in progress'
            return status
        except:
            return 'in progress'



class FomopayPaymentResponseView(EdxOrderPlacementMixin, View):
    """ Starts FOMO Pay payment process.

    This view is intended to be called asynchronously by the payment processor.
    The view expects POST data containing a transaction ID and the payment result
    to complete the fulfillment pipeline.
    """

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
        try:
            notification = request.POST.dict()
            basket = self.validate_notification(notification)

        except DuplicateReferenceNumber:
            return self.redirect_to_receipt_page(notification)
        except TransactionDeclined:
            order_number = request.POST.get('transaction')
            old_basket_id = OrderNumberGenerator().basket_id(order_number)
            old_basket = Basket.objects.get(id=old_basket_id)

            new_basket = Basket.objects.create(owner=old_basket.owner, site=request.site)

            # We intentionally avoid thawing the old basket here to prevent order
            # numbers from being reused. For more, refer to commit a1efc68.
            new_basket.merge(old_basket, add_quantities=False)

            message = _(
                'An error occurred while processing your payment. You have not been charged. '
                'Please double-check your WeChat app and try again. '
                'For help, {link_start}contact support{link_end}.'
            ).format(
                link_start='<a href="{}">'.format(request.site.siteconfiguration.payment_support_url),
                link_end='</a>',
            )

            messages.error(request, mark_safe(message))

            return redirect(reverse('basket:summary'))
        except:  # pylint: disable=bare-except
            return redirect(reverse('payment_error'))

        try:
            order = self.create_order(request, basket, self._get_billing_address(notification))
            self.handle_post_order(order)

            # return self.redirect_to_receipt_page(notification)
        except:  # pylint: disable=bare-except
            return redirect(reverse('payment_error'))



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
            order_number = notification.get('transaction')
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
                    'Received an invalid FOMO Pay response. The payment response was recorded in entry [%d].',
                    ppr.id
                )
                raise
            except (UserCancelled, TransactionDeclined) as exception:
                logger.info(
                    'FOMO Pay payment [%d] did not complete for basket [%d] because [%s]. '
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

    def _get_billing_address(self, fomopay_response):
        """ Fill in the billing address using the payment notification.

        FOMO Pay doesn't provide a billing address in the payment notification,
        and by the e-commerce platform design this field can't be None nor empty,
        so as a temporal address we're storing the payment id.
        """
        return BillingAddress(
            first_name='N/A',
            last_name='N/A',
            line1=fomopay_response['payment_id'],

            # Oscar uses line4 for city
            line4=fomopay_response['payment_id'],
            country=Country.objects.get(
                iso_3166_1_a2='SG'))
