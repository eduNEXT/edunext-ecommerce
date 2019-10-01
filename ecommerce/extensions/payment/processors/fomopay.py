"""FOMO Pay payment processing."""
import logging
import uuid
from hashlib import sha256

from django.conf import settings
from django.urls import reverse
from oscar.core.loading import get_class, get_model

from ecommerce.extensions.payment.processors import BasePaymentProcessor

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
        pass

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
