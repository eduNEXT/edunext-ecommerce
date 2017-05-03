""" PayU payment processing views """
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from oscar.apps.partner import strategy
from oscar.apps.payment.exceptions import PaymentError, TransactionDeclined
from oscar.core.loading import get_class, get_model

from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.exceptions import InvalidSignatureError
from ecommerce.extensions.payment.processors.payu import Payu

logger = logging.getLogger(__name__)

Applicator = get_class('offer.applicator', 'Applicator')
Basket = get_model('basket', 'Basket')
BillingAddress = get_model('order', 'BillingAddress')
Country = get_model('address', 'Country')
NoShippingRequired = get_class('shipping.methods', 'NoShippingRequired')
OrderNumberGenerator = get_class('order.utils', 'OrderNumberGenerator')
OrderTotalCalculator = get_class('checkout.calculators', 'OrderTotalCalculator')


class PayUPaymentResponseView(EdxOrderPlacementMixin, View):
    """ Validates a response from PayU and processes the associated basket/order appropriately. """

    @property
    def payment_processor(self):
        return Payu(self.request.site)

    # Disable atomicity for the view. Otherwise, we'd be unable to commit to the database
    # until the request had concluded; Django will refuse to commit when an atomic() block
    # is active, since that would break atomicity. Without an order present in the database
    # at the time fulfillment is attempted, asynchronous order fulfillment tasks will fail.
    @method_decorator(transaction.non_atomic_requests)
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(PayUPaymentResponseView, self).dispatch(request, *args, **kwargs)

    def _get_billing_address(self, payu_response):

        return BillingAddress(
            first_name=payu_response.get('cc_holder', ''),
            last_name=payu_response.get('cc_holder', ''),
            line1=payu_response['billing_address'],

            # Oscar uses line4 for city
            line4=payu_response['billing_city'],
            country=Country.objects.get(
                iso_3166_1_a2=payu_response['billing_country']))

    def _get_basket(self, basket_id):
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

    def post(self, request):
        """Process a PayU merchant notification and place an order for paid products as appropriate."""

        # Note (CCB): Orders should not be created until the payment processor has validated the response's signature.
        # This validation is performed in the handle_payment method. After that method succeeds, the response can be
        # safely assumed to have originated from PayU.
        payu_response = request.POST.dict()
        basket = None
        transaction_id = None

        try:
            transaction_id = payu_response.get('transaction_id')
            order_number = payu_response.get('reference_sale')
            basket_id = OrderNumberGenerator().basket_id(order_number)

            logger.info(
                'Received PayU merchant notification for transaction [%s], associated with basket [%d].',
                transaction_id,
                basket_id
            )

            basket = self._get_basket(basket_id)

            if not basket:
                logger.error('Received payment for non-existent basket [%s].', basket_id)
                return HttpResponse(status=400)
        finally:
            # Store the response in the database.
            ppr = self.payment_processor.record_processor_response(payu_response, transaction_id=transaction_id,
                                                                   basket=basket)

        try:
            # Explicitly delimit operations which will be rolled back if an exception occurs.
            with transaction.atomic():
                try:
                    self.handle_payment(payu_response, basket)
                except InvalidSignatureError:
                    logger.exception(
                        'Received an invalid PayU response. The payment response was recorded in entry [%d].',
                        ppr.id
                    )
                    return HttpResponse(status=400)
                except TransactionDeclined as exception:
                    logger.info(
                        'PayU payment did not complete for basket [%d] because [%s]. '
                        'The payment response was recorded in entry [%d].',
                        basket.id,
                        exception.__class__.__name__,
                        ppr.id
                    )
                    return HttpResponse()
                except PaymentError:
                    logger.exception(
                        'PayU payment failed for basket [%d]. The payment response was recorded in entry [%d].',
                        basket.id,
                        ppr.id
                    )
                    return HttpResponse()
        except:  # pylint: disable=bare-except
            logger.exception('Attempts to handle payment for basket [%d] failed.', basket.id)
            return HttpResponse(status=200)

        try:
            # Note (CCB): In the future, if we do end up shipping physical products, we will need to
            # properly implement shipping methods. For more, see
            # http://django-oscar.readthedocs.org/en/latest/howto/how_to_configure_shipping.html.
            shipping_method = NoShippingRequired()
            shipping_charge = shipping_method.calculate(basket)

            # Note (CCB): This calculation assumes the payment processor has not sent a partial authorization,
            # thus we use the amounts stored in the database rather than those received from the payment processor.
            user = basket.owner
            order_total = OrderTotalCalculator().calculate(basket, shipping_charge)
            billing_address = self._get_billing_address(payu_response)

            self.handle_order_placement(
                order_number,
                user,
                basket,
                None,
                shipping_method,
                shipping_charge,
                billing_address,
                order_total,
                request=request,
            )

            return HttpResponse()
        except:  # pylint: disable=bare-except
            payment_processor = self.payment_processor.NAME.title() if self.payment_processor else None
            logger.exception(self.order_placement_failure_msg, payment_processor, basket.id)
            return HttpResponse(status=200)

    def get(self, request, *args, **kwargs):
        # pylint: disable=unused-argument
        """Handle an incoming user returned to us by PayU after processing payment."""

        payu_response = request.GET.dict()
        try:
            transaction_id = payu_response.get('transactionId')
            order_number = payu_response.get('referenceCode')
            basket_id = OrderNumberGenerator().basket_id(order_number)

            logger.info(
                'Received PayU payer notification for transaction [%s], associated with basket [%d].',
                transaction_id,
                basket_id
            )

            basket = self._get_basket(basket_id)

            if not basket:
                logger.error('Received payer notification for non-existent basket [%s].', basket_id)
                return redirect(reverse('payment_error'))
        except:  # pylint: disable=bare-except
            return redirect(reverse('payment_error'))

        receipt_url = get_receipt_page_url(
            order_number=basket.order_number,
            site_configuration=basket.site.siteconfiguration
        )

        try:
            return redirect(receipt_url)
        except:  # pylint: disable=bare-except
            payment_processor = self.payment_processor.NAME.title() if self.payment_processor else None
            logger.exception(self.order_placement_failure_msg, payment_processor, basket.id)
            return redirect(receipt_url)
