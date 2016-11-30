# -*- coding: utf-8 -*-
"""Unit tests of PayU payment processor implementation."""

from oscar.test import factories
from oscar.core.loading import get_model

from ecommerce.extensions.payment.tests.mixins import PayuMixin
from ecommerce.extensions.payment.processors.payu import Payu
from ecommerce.extensions.payment.tests.processors.mixins import PaymentProcessorTestCaseMixin
from ecommerce.extensions.payment.exceptions import InvalidSignatureError
from ecommerce.tests.testcases import TestCase

PaymentEventType = get_model('order', 'PaymentEventType')
SourceType = get_model('payment', 'SourceType')


class PayuTests(PayuMixin, PaymentProcessorTestCaseMixin, TestCase):
    """ Tests for PayU payment processor. """

    processor_class = Payu
    processor_name = 'payu'

    def test_get_transaction_parameters(self):
        """ Verify the processor returns the appropriate parameters required to complete a transaction. """

        required_parameters = [
            'payment_page_url',
            'merchantId',
            'accountId',
            'ApiKey',
            'referenceCode',
            'tax',
            'taxReturnBase',
            'currency',
            'description',
            'buyerEmail',
            'buyerFullName',
            'amount',
            'responseUrl',
            'confirmationUrl',
            'signature'
        ]

        if self.processor.test:
            required_parameters.append('test')

        transaction_parameters = self.processor.get_transaction_parameters(
            self.basket)

        self.assertEqual(set(required_parameters), set(transaction_parameters.keys()))

    def test_handle_processor_response(self):
        """ Verify that the processor creates the appropriate PaymentEvent and Source objects. """
        # pylint: disable=protected-access
        response = self.generate_response(self.basket)
        reference = response['transaction_id']
        response['sign'] = self.processor._generate_signature(response,
                                                              self.processor.CONFIRMATION_SIGNATURE)
        source, payment_event = self.processor.handle_processor_response(response, basket=self.basket)

        # Validate the Source
        source_type = SourceType.objects.get(code=self.processor.NAME)
        label = response['cc_number']
        self.assert_basket_matches_source(
            self.basket,
            source,
            source_type,
            reference,
            label
        )

        # Validate PaymentEvent
        paid_type = PaymentEventType.objects.get(code='paid')
        amount = self.basket.total_incl_tax
        self.assert_valid_payment_event_fields(payment_event, amount, paid_type, self.processor.NAME, reference)

    def test_handle_processor_response_invalid_signature(self):
        """
        The handle_processor_response method should raise an InvalidSignatureError if the response's
        signature is not valid.
        """
        response = self.generate_response(self.basket)
        response['signature'] = 'Tampered.'
        self.assertRaises(InvalidSignatureError,
                          self.processor.handle_processor_response,
                          response,
                          basket=self.basket)

    def test_issue_credit(self):
        """ Verify the payment processor responds appropriately to requests to issue credit. """

        amount = 123
        currency = 'USD'
        source = 'test-source'

        self.assertRaises(NotImplementedError,
                          self.processor.issue_credit,
                          source,
                          amount,
                          currency)

    def test_issue_credit_error(self):
        """ Verify the payment processor responds appropriately if the payment gateway cannot issue a credit. """

        amount = 123
        currency = 'USD'
        source = 'test-source'

        self.assertRaises(NotImplementedError,
                          self.processor.issue_credit,
                          source,
                          amount,
                          currency)

    def test_get_single_seat(self):
        """
        The single-seat helper for payu reporting should correctly
        and return the first 'seat' product encountered in a basket.
        """
        get_single_seat = Payu.get_single_seat

        # finds the seat when it's the only product in the basket.
        self.assertEqual(get_single_seat(self.basket), self.product)

        # finds the first seat added, when there's more than one.
        basket = factories.create_basket(empty=True)
        other_seat = factories.ProductFactory(
            product_class=self.seat_product_class,
            stockrecords__price_currency='USD',
            stockrecords__partner__short_code='test',
        )
        basket.add_product(self.product)
        basket.add_product(other_seat)
        self.assertEqual(get_single_seat(basket), self.product)

        # finds the seat when there's a mixture of product classes.
        basket = factories.create_basket(empty=True)
        other_product = factories.ProductFactory(
            stockrecords__price_currency='USD',
            stockrecords__partner__short_code='test2',
        )
        basket.add_product(other_product)
        basket.add_product(self.product)
        self.assertEqual(get_single_seat(basket), self.product)
        self.assertNotEqual(get_single_seat(basket), other_product)

        # returns None when there's no seats.
        basket = factories.create_basket(empty=True)
        basket.add_product(other_product)
        self.assertIsNone(get_single_seat(basket))

        # returns None for an empty basket.
        basket = factories.create_basket(empty=True)
        self.assertIsNone(get_single_seat(basket))

    def test_is_signature_valid(self):
        """ Verify that the is_signature_valid method properly validates the response's signature. """

        # Empty data should never be valid
        self.assertFalse(self.processor.is_signature_valid({}))

        # The method should return False for responses with invalid signatures.
        response = {
            'reference_sale': 'test_reference_sale',
            'value': '123',
            'currency': 'USD',
            'sign': 'invalid_signature',
            'state_pol': '6'
        }
        self.assertFalse(self.processor.is_signature_valid(response))

        # The method should return True for example responses on Payu developers site
        self.processor.api_key = '4Vj8eK4rloUd272L48hsrarnUA'
        self.processor.merchant_id = '508029'

        response = {
            'reference_sale': 'TestPayU04',
            'value': '150.00',
            'currency': 'USD',
            'sign': 'df67936f918887b2aa31688a77a10fe1',
            'state_pol': '6'
        }

        self.assertTrue(self.processor.is_signature_valid(response))

        # Now testing the case when value has two decimals and different state
        response = {
            'reference_sale': 'TestPayU05',
            'value': '150.26',
            'currency': 'USD',
            'sign': '1d95778a651e11a0ab93c2169a519cd6',
            'state_pol': '4'
        }

        self.assertTrue(self.processor.is_signature_valid(response))

    def test_generate_signature(self):
        """ Verify that payment form signature is correct """

        # pylint: disable=protected-access
        self.processor.api_key = '4Vj8eK4rloUd272L48hsrarnUA'
        self.processor.merchant_id = '508029'
        expected_signature = 'ba9ffa71559580175585e45ce70b6c37'

        parameters = {
            'referenceCode': 'TestPayU',
            'amount': '3',
            'currency': 'USD',
            'accountId': '512326',
            'buyerEmail': 'test@test.com'
        }

        signature = self.processor._generate_signature(parameters,
                                                       self.processor.PAYMENT_FORM_SIGNATURE)

        self.assertEqual(signature, expected_signature)
