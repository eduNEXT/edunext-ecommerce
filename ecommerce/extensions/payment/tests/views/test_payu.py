""" Tests of the Payment Views. """
import ddt
import mock

from django.core.urlresolvers import reverse

from oscar.test import factories
from oscar.apps.payment.exceptions import PaymentError, TransactionDeclined
from oscar.core.loading import get_model
from testfixtures import LogCapture

from ecommerce.extensions.payment.tests.mixins import PaymentEventsMixin, PayuMixin
from ecommerce.extensions.payment.processors.payu import Payu
from ecommerce.extensions.payment.views.payu import PayUPaymentResponseView
from ecommerce.tests.testcases import TestCase

Order = get_model('order', 'Order')
PaymentEventType = get_model('order', 'PaymentEventType')
SourceType = get_model('payment', 'SourceType')


@ddt.ddt
class PayUPaymentResponseViewTests(PayuMixin, PaymentEventsMixin, TestCase):
    """ Test processing of PayU notifications. """

    TRANSACTION_DECLINED = '6'
    TRANSACTION_ERROR = '104'

    def setUp(self):
        super(PayUPaymentResponseViewTests, self).setUp()

        self.user = factories.UserFactory()

        self.basket = factories.create_basket()
        self.basket.site = self.site
        self.basket.owner = self.user
        self.basket.freeze()

        self.processor = Payu(self.site)
        self.processor_name = self.processor.NAME

    def _assert_processing_failure(self, notification, status_code, error_message, log_level='ERROR'):
        """Verify that payment processing operations fail gracefully."""
        logger_name = 'ecommerce.extensions.payment.views.payu'
        with LogCapture(logger_name) as log_capture:
            response = self.client.post(reverse('payu_notify'), notification)

            self.assertEqual(response.status_code, status_code)

            self.assert_processor_response_recorded(
                self.processor_name,
                notification[u'transaction_id'],
                notification,
                basket=self.basket
            )

            log_capture.check(
                (
                    logger_name,
                    'INFO',
                    'Received PayU merchant notification for transaction [{transaction_id}], '
                    'associated with basket [{basket_id}].'.format(
                        transaction_id=notification[u'transaction_id'],
                        basket_id=self.basket.id
                    )
                ),
                (logger_name, log_level, error_message)
            )

    @ddt.data(
        (PaymentError, 200, 'ERROR', 'PayU payment failed for basket [{basket_id}]. '
                                     'The payment response was recorded in entry [{response_id}].'),
        (TransactionDeclined, 200, 'INFO', 'PayU payment did not complete for basket [{basket_id}] because '
                                           '[TransactionDeclined]. The payment response was recorded in entry '
                                           '[{response_id}].'),
        (KeyError, 500, 'ERROR', 'Attempts to handle payment for basket [{basket_id}] failed.')
    )
    @ddt.unpack
    def test_payment_handling_error(self, error_class, status_code, log_level, error_message):
        """
        Verify that PayU's merchant notification is saved to the database despite an error handling payment.
        """
        notification = self.generate_response(self.basket)
        with mock.patch.object(
            PayUPaymentResponseView,
            'handle_payment',
            side_effect=error_class
        ) as fake_handle_payment:
            self._assert_processing_failure(
                notification,
                status_code,
                error_message.format(basket_id=self.basket.id, response_id=1),
                log_level
            )
            self.assertTrue(fake_handle_payment.called)

    def _assert_payment_data_recorded(self, notification):
        """ Ensure PaymentEvent, PaymentProcessorResponse, and Source objects are created for the basket. """

        # Ensure the response is stored in the database
        self.assert_processor_response_recorded(self.processor_name, notification[u'transaction_id'], notification,
                                                basket=self.basket)

        # Validate a payment Source was created
        reference = notification[u'transaction_id']
        source_type = SourceType.objects.get(code=self.processor_name)
        label = notification[u'cc_number']
        self.assert_payment_source_exists(self.basket, source_type, reference, label)

        # Validate that PaymentEvents exist
        paid_type = PaymentEventType.objects.get(code='paid')
        self.assert_payment_event_exists(self.basket, paid_type, reference, self.processor_name)

    @ddt.data(
        TRANSACTION_ERROR,
        TRANSACTION_DECLINED,
        'blah!'
    )
    @mock.patch('ecommerce.extensions.payment.processors.payu.Payu.is_signature_valid')
    def test_not_accepted(self, transaction_state, is_valid_mock):
        """
        When payment is NOT accepted, the processor's response should be saved to the database. An order should NOT
        be created.
        """
        is_valid_mock.return_value = True
        notification = self.generate_response(self.basket, transaction_state=transaction_state)
        response = self.client.post(reverse('payu_notify'), notification)

        # The view should always return 200
        self.assertEqual(response.status_code, 200)

        # The basket should not have an associated order if no payment was made.
        self.assertFalse(Order.objects.filter(basket=self.basket).exists())

        # Ensure the response is stored in the database
        self.assert_processor_response_recorded(self.processor_name, notification[u'transaction_id'], notification,
                                                basket=self.basket)
