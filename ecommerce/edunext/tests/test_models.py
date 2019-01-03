"""
Test file for SiteOptions model.
"""

from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError

from ecommerce.tests.testcases import TestCase
from ecommerce.edunext.models import SiteOptions


def _make_site_options(blob_str, site_id=1):
    site = Site.objects.get(id=site_id)

    return SiteOptions(
        site=site,
        options_blob=blob_str,
    )


class SiteOptionsTests(TestCase):
    """
    Test class for SiteOptions Model.
    """
    def test_options_blob_validation_success(self):
        """
        Tests that validation passes when creating a field with a correct value
        """
        try:
            site_options = _make_site_options({"ThisIs": "ValidJson"})
            site_options.clean_fields()
        except ValidationError:
            self.fail("A validation error ocurred, when none where expected")
