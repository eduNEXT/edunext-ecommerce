"""FOMO Pay payment processing."""
import logging
import uuid
from decimal import Decimal
from hashlib import sha256

from django.conf import settings
from django.urls import reverse
from oscar.apps.payment.exceptions import GatewayError, TransactionDeclined, UserCancelled
from oscar.core.loading import get_class, get_model

from ecommerce.extensions.payment.exceptions import (
    AuthorizationError,
    DuplicateReferenceNumber,
    InvalidSignatureError,
    PartialAuthorizationError
)
from ecommerce.extensions.payment.processors import BasePaymentProcessor, HandledProcessorResponse

logger = logging.getLogger(__name__)

Order = get_model('order', 'Order')
OrderNumberGenerator = get_class('order.utils', 'OrderNumberGenerator')


class Fomopay(BasePaymentProcessor):
    """FOMO Pay payment processor (September 2019).

    For reference, see
    https://developers.fomopay.com/docs/api/wechat/qr
    """

    NAME = 'fomopay'

    def __init__(self, site):
        """
        Constructs a new instance of the FOMO Pay processor.

        Raises:
            KeyError: If no settings configured for this payment processor
        """

        super(Fomopay, self).__init__(site)

        configuration = self.configuration
        self.merchant = configuration['api_username']
        self.timeout = configuration['timeout']
        self.callback_url = configuration['callback_url']
        self.type = configuration['type']
        self.api_key = configuration['api_key']
        self.api_url = configuration['api_url']

    def get_transaction_parameters(self, basket, request=None, use_client_side_checkout=False, **kwargs):
        """
        Generate a dictionary of signed parameters FOMO Pay requires to complete a transaction.

        Arguments:
            basket (Basket): The basket of products being purchased.

        Returns:
            dict: Payment processor-specific parameters required to complete a transaction.
        """

        parameters = {
            'merchant': self.merchant,
            'price': str(basket.total_incl_tax),
            'description': self.get_basket_description(basket),
            'transaction': basket.order_number,
            'callback_url': self.callback_url,
            'currency_code': basket.currency.lower(),
            'type': self.type,
            'timeout': self.timeout,
            'nonce': uuid.uuid4().hex,
        }

        parameters['signature'] = self._generate_signature(parameters)
        parameters['payment_page_url'] = reverse('fomopay:payment')
        parameters['api_url'] = self.api_url
        return parameters

    def handle_processor_response(self, response, basket=None):
        """
        Handle a response (i.e., "merchant notification") from FOMO Pay.

        This method does the following:
            1. Verify the validity of the response.
            2. Create PaymentEvents and Sources for successful payments.

        Arguments:
            response (dict): Dictionary of parameters received from the payment processor.

        Keyword Arguments:
            basket (Basket): Basket being purchased via the payment processor.

        Raises:
            TransactionDeclined: Indicates the payment was declined by the processor.
            GatewayError: Indicates a general error on the part of the processor.
        """

        # Validate the signature
        if not self.is_signature_valid(response):
            raise InvalidSignatureError

        # Raise an exception for payments that were not accepted. Consuming code should be responsible for handling
        # and logging the exception.
        decision = response['result']
        if decision != '0':
            # FOMO Pay is not explicit to say what is the cause of the error,
            # it is necessary that we make our own checks.

            # Check if the user made a payment request twice for the same order.
            if Order.objects.filter(number=response['transaction']).exists():
                raise DuplicateReferenceNumber

            # Raise an exception if the authorized amount differs from the requested amount.
            if response.get('cash_amount') and response['cash_amount'] != basket.total_incl_tax:
                raise PartialAuthorizationError

            raise {
                'cancel': UserCancelled,
                'decline': TransactionDeclined,
                'error': GatewayError,
                'review': AuthorizationError,
            }.get(decision, InvalidFomoPayDecision)

        currency = response.get('cash_currency', basket.currency)
        total = Decimal(response.get('cash_amount', basket.total_incl_tax))
        transaction_id = response.get('payment_id', None)

        return HandledProcessorResponse(
            transaction_id=transaction_id,
            total=total,
            currency=currency,
            card_type='WeChat QR Payment',
            card_number='WeChat QR Payment'
        )

    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        pass

    def _generate_signature(self, parameters):
        """
        Sign the contents of the provided transaction parameters dictionary.

        This allows FOMO Pay to verify that the transaction parameters have not been tampered with
        during transit.

        We also use this signature to verify that the signature we get back from FOMO Pay is valid for
        the parameters that they are giving to us.

        Arguments:
            parameters (dict): A dictionary of transaction parameters.

        Returns:
            unicode: the signature for the given parameters
        """
        sorted_params = []

        for key in sorted(parameters):
            sorted_params.append('{}={}'.format(key, parameters[key]))

        query_str = '&'.join(sorted_params)
        query_str = '{}&shared_key={}'.format(query_str, self.api_key)

        return sha256(query_str).hexdigest()

    def is_signature_valid(self, response):
        """Returns a boolean indicating if the response's signature (indicating potential tampering) is valid."""

        response_signature = response.pop('signature', None)

        if not response_signature:
            return False

        return self._generate_signature(response) == response_signature

    @staticmethod
    def get_basket_description(basket):
        """
        Return a string representation defined by product ids (course_id)
        present in the basket.

        Arguments:
            basket (Basket): The basket of products being purchased.
        """

        description = []
        for line in basket.all_lines():
            description.append(line.product.course_id)

        return "Seat(s) bought in:{}".format(",".join(description))


class InvalidFomoPayDecision(GatewayError):
    """The decision returned by FOMO Pay was not recognized."""
    pass
