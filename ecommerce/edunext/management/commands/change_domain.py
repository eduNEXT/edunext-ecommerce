"""
This module contains the command class to change
the subdomain from prod domains to stage versions.
"""
import json
import logging

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

try:
    from urllib.parse import urlparse  # Python 3 Compatible
except ImportError:
    from urlparse import urlparse  # Python 2 Compatible

LOGGER = logging.getLogger(__name__)
CHANGE_DOMAIN_DEFAULT_SITE_NAME = 'stage.edunext.co'


class Command(BaseCommand):
    """
    This class contains the methods to change
    site prod domains to a stage version.
    """
    help = """This function will iterate over all Site objects
            to change Site prod domains to a stage version."""
    suffix_stage_domain = ""

    def add_arguments(self, parser):
        """
        Add optional domain from the line command
        """
        parser.add_argument('suffix_domain', type=str,
                            nargs='?', default=CHANGE_DOMAIN_DEFAULT_SITE_NAME,
                            help='Suffix domain appended to ecommerce domains')
        parser.add_argument('suffix_lms_domain', type=str,
                            nargs='?', default=CHANGE_DOMAIN_DEFAULT_SITE_NAME,
                            help='Suffix domain appended to LMS domains')

    def handle(self, *args, **options):
        """
        This method will iterate over all Sites and SiteConfiguration
        objects to change Site prod domains to a stage version.
        """
        self.suffix_stage_domain = options['suffix_domain']
        self.suffix_stage_lms_domain = options['suffix_lms_domain']  # pylint: disable=attribute-defined-outside-init

        for site in Site.objects.all():
            orig_domain = site.domain
            stage_domain = self.change_subdomain(orig_domain)

            if stage_domain:
                site.domain = stage_domain
                site.name = (orig_domain + u' stage')[:50]  # Name field limited to 50 characters
                site.save()

            # Now the lms urls are changed on the SiteConfiguration object
            lms_url_root = site.siteconfiguration.lms_url_root
            prod_lms_domain = urlparse(lms_url_root).netloc

            stage_lms_domain = self.change_subdomain(prod_lms_domain, self.suffix_stage_lms_domain)

            if stage_lms_domain:
                oauth_settings_string = json.dumps(site.siteconfiguration.oauth_settings)
                # Replacing all concidences of the LMS prod domain inside the
                # configurations by the stage domain
                mod_oauth_settings_string = oauth_settings_string.replace(
                    prod_lms_domain,
                    stage_lms_domain
                )
                site.siteconfiguration.oauth_settings = json.loads(mod_oauth_settings_string)
                site.siteconfiguration.lms_url_root = lms_url_root.replace(
                    prod_lms_domain,
                    stage_lms_domain
                )
                site.siteconfiguration.save()

    def change_subdomain(self, subdomain, suffix_domain=None):
        """
        Transforming the domain to format
        my-site-domain-{suffix_domain}
        """
        if not suffix_domain:
            suffix_domain = self.suffix_stage_domain

        domain = self.strip_port_from_host(subdomain)

        # Don't bother on changing anything if the suffix is correct
        if domain.endswith(suffix_domain):
            return ""

        port = None
        if ':' in subdomain:
            port = subdomain.split(':')[1]

        pre_formatted = "{}-{}"
        if suffix_domain.startswith("."):
            pre_formatted = "{}{}"
        try:
            stage_domain = pre_formatted.format(
                domain.replace('.', '-'),
                suffix_domain
            )
            if port:
                stage_domain += ':' + port
        except TypeError as exc:
            stage_domain = ""
            message = u"Unable to define stage url for site {}".format(
                subdomain
            )
            LOGGER.warning(message)
            LOGGER.error(exc.message)  # pylint: disable=no-member
        return stage_domain

    def strip_port_from_host(self, host):
        """
        Strips the port from a given host
        """
        return host.split(':')[0]
