#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import MagicMock, patch

from django.test.utils import override_settings
from django.contrib.sites.models import Site

from ecommerce.tests.testcases import TestCase
from ecommerce.edunext.models import SiteOptions
from ecommerce.edunext.conf import settings as SiteSettings


def _make_site(blob_str=None, site_id=1):
    """
    Returns a site object. If blob_str is passed, a SiteOptions object
    related to the site is created or updated with the blob, otherwise,
    existent SiteOptions object for the site is deleted
    """
    site = Site.objects.get(id=site_id)

    if blob_str is not None:
        obj, _ = SiteOptions.objects.get_or_create(
            site=site
        )
        obj.options_blob = blob_str
        obj.save()
    else:
        SiteOptions.objects.filter(site=site).delete()

    return site


class EdunextConfTests(TestCase):
    """
    Test for Edunext site aware configurations
    """

    @override_settings(OSCAR_DEFAULT_CURRENCY="CAD")
    @patch("ecommerce.edunext.conf.get_current_request")
    def test_conf_without_siteoptions(self, get_current_request_mock):
        request_mock = MagicMock()
        request_mock.site = _make_site()
        get_current_request_mock.return_value = request_mock
        self.assertEqual(SiteSettings.OSCAR_DEFAULT_CURRENCY, "CAD")

    @override_settings(OSCAR_DEFAULT_CURRENCY="COP")
    @patch("ecommerce.edunext.conf.get_current_request")
    def test_conf_with_siteoptions_no_overide(self, get_current_request_mock):
        request_mock = MagicMock()
        site_options = {
            "ANY_OTHER_SETTING": "any_value"
        }
        request_mock.site = _make_site(site_options)
        get_current_request_mock.return_value = request_mock
        self.assertEqual(SiteSettings.OSCAR_DEFAULT_CURRENCY, "COP")

    @override_settings(OSCAR_DEFAULT_CURRENCY="USD")
    @patch("ecommerce.edunext.conf.get_current_request")
    def test_conf_with_siteoptions_overide(self, get_current_request_mock):
        request_mock = MagicMock()
        site_options = {
            "OSCAR_DEFAULT_CURRENCY": "BRL"
        }
        request_mock.site = _make_site(site_options)
        get_current_request_mock.return_value = request_mock
        self.assertEqual(SiteSettings.OSCAR_DEFAULT_CURRENCY, "BRL")
