import hashlib

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

from edx_rest_api_client.client import EdxRestApiClient

from ecommerce.core.url_utils import get_lms_url
from ecommerce.core.utils import traverse_pagination


def mode_for_seat(product):
    """
    Returns the enrollment mode (aka course mode) for the specified product.
    If the specified product does not include a 'certificate_type' attribute it is likely the
    bulk purchase "enrollment code" product variant of the single-seat product, so we attempt
    to locate the 'seat_type' attribute in its place.
    """
    mode = getattr(product.attr, 'certificate_type', getattr(product.attr, 'seat_type', None))
    if not mode:
        return 'audit'
    if mode == 'professional' and not getattr(product.attr, 'id_verification_required', False):
        return 'no-id-professional'
    return mode


def get_course_info_from_lms(course_key):
    """ Get course information from LMS via the course api and cache """
    api = EdxRestApiClient(get_lms_url('api/courses/v1/'))
    cache_key = 'courses_api_detail_{}'.format(course_key)
    cache_hash = hashlib.md5(cache_key).hexdigest()
    course = cache.get(cache_hash)
    if not course:  # pragma: no cover
        course = api.courses(course_key).get()
        cache.set(cache_hash, course, settings.COURSES_API_CACHE_TIMEOUT)
    return course


def get_course_catalogs(site, resource_id=None):
    """
    Get details related to course catalogs from Catalog Service.

    Arguments:
        site (Site): Site object containing Site Configuration data
        resource_id (int or str): Identifies a specific resource to be retrieved

    Returns:
        dict: Course catalogs received from Course Catalog API

    Raises:
        ConnectionError: requests exception "ConnectionError"
        SlumberBaseException: slumber exception "SlumberBaseException"
        Timeout: requests exception "Timeout"

    """
    resource = 'catalogs'
    base_cache_key = '{}.catalog.api.data'.format(site.domain)

    cache_key = '{}.{}'.format(base_cache_key, resource_id) if resource_id else base_cache_key
    cache_key = hashlib.md5(cache_key).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        return cached

    api = site.siteconfiguration.course_catalog_api_client
    endpoint = getattr(api, resource)
    response = endpoint(resource_id).get()

    if resource_id:
        results = response
    else:
        results = traverse_pagination(response, endpoint)

    cache.set(cache_key, results, settings.COURSES_API_CACHE_TIMEOUT)
    return results


def get_certificate_type_display_value(certificate_type):
    display_values = {
        'audit': _('Audit'),
        'credit': _('Credit'),
        'honor': _('Honor'),
        'professional': _('Professional'),
        'verified': _('Verified'),
    }

    if certificate_type not in display_values:
        raise ValueError('Certificate Type [%s] not found.', certificate_type)

    return display_values[certificate_type]
