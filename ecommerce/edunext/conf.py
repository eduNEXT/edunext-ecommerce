"""
This file implements a class which is a handy utility to make any
call to the settings completely site aware by replacing the:

from django.conf import settings

with:

from ecommerce.edunext.conf import settings

"""
from threadlocals.threadlocals import get_current_request

from django.conf import settings as base_settings

from ecommerce.edunext.models import SiteOptions


class SiteAwareSettings(object):
    """
    This class is a proxy object of the settings object from django.
    It will try to get a value from the microsite and default to the
    django settings
    """

    def get_current_request_site_options(self):
        """
        This method retrieves the edunext options for current request site
        """
        site = get_current_request().site
        try:
            options = site.siteoptions.options_blob
        except SiteOptions.DoesNotExist:
            # May be log some message
            options = {}

        return options

    def __getattr__(self, name):
        current_site_options = self.get_current_request_site_options()
        try:
            return current_site_options.get(name, getattr(base_settings, name))
        except KeyError:
            return getattr(base_settings, name)


settings = SiteAwareSettings()  # pylint: disable=invalid-name