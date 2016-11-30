from threadlocals.threadlocals import get_current_request

from ecommerce.tests.testcases import TestCase
from ecommerce.edunext.context_processors import theme_options


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
