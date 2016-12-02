import ddt

from threadlocals.threadlocals import get_current_request
from django.contrib.sites.models import Site

from ecommerce.edunext.models import SiteOptions
from ecommerce.tests.testcases import TestCase
from ecommerce.edunext.context_processors import theme_options


@ddt.ddt
class TestThemeOptions(TestCase):

    def test_theme_options_signature(self):
        """
        Tests that theme_options returns a dict no matter what
        """
        request = get_current_request()
        result = theme_options(request)
        self.assertIsInstance(result, dict)

    def test_theme_options_contains_basics(self):
        """
        Tests that theme_options returns the theme_dir_name, siteconfiguration and options
        """
        request = get_current_request()
        result = theme_options(request)

        for x in ['theme_dir_name', 'site_configuration', 'options']:
            self.assertIn(x, result)

    @ddt.data(
        {"a": "test"},
        {"theming_var": "http://some.example.com/test.jpg"},
    )
    def test_theme_options_contains_options(self, test_dict):
        """
        Tests that theme_options returns the options dictionary into the options key
        """
        site = Site.objects.get(id=1)
        SiteOptions(
            site=site,
            options_blob=test_dict,
        ).save()

        request = get_current_request()
        result = theme_options(request)

        self.assertIsInstance(result.get("options"), dict)
        self.assertEqual(result.get("options"), test_dict)
