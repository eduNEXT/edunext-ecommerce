#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import patch

from ecommerce.tests.testcases import TestCase

from ecommerce.edunext.utils import (
    disable_translation,
    ednx_currency,
)


class EdunextUtilsTests(TestCase):
    """
    Test for Edunext utils functions
    """

    def test_disable_translation(self):
        val = "some_string"
        self.assertEqual(val, disable_translation(val))

    @patch("ecommerce.edunext.utils.oscar_currency")
    def test_ednx_currency(self, mock_oscar_currency):

        unicode_val = u"10.45\xa0USD"
        mock_oscar_currency.return_value = unicode_val
        result = ednx_currency(u"10")
        self.assertTrue(isinstance(result, str))
