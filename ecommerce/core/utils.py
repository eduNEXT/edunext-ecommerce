

import logging
from urllib.parse import parse_qs, urlparse

import waffle
from django.conf import settings
from django.core.exceptions import ValidationError
from edx_django_utils.cache import get_cache_key as get_django_cache_key

logger = logging.getLogger(__name__)


def log_message_and_raise_validation_error(message):
    """
    Logs provided message and raises a ValidationError with the same message.

    Args:
        message (str): Message to be logged and handled by the ValidationError.

    Raises:
        ValidationError: Raise with message provided by developer.
    """
    logger.error(message)
    raise ValidationError(message)


def get_cache_key(**kwargs):
    """
    Wrapper method on edx_django_utils get_cache_key utility.
    """
    return get_django_cache_key(**kwargs)


def deprecated_traverse_pagination(response, client, api_url):
    """
    Traverse a paginated API response.

    Note: This method should be deprecated since it defeats the purpose
    of pagination.

    Extracts and concatenates "results" (list of dict) returned by DRF-powered
    APIs.

    Arguments:
        response (Dict): Current response dict from service API
        client (requests.Session): OAuthAPIClient object from edx-rest-api-client
        api_url (str): API endpoint URL

    Returns:
        list of dict.

    """
    results = response.get('results', [])

    next_page = response.get('next')
    while next_page:
        if waffle.switch_is_active("debug_logging_for_deprecated_traverse_pagination"):  # pragma: no cover
            logger.info("deprecated_traverse_pagination method is called for endpoint %s", api_url)
        querystring = parse_qs(urlparse(next_page).query, keep_blank_values=True)
        response = client.get(api_url, params=querystring)
        response.raise_for_status()
        response = response.json()
        results += response.get('results', [])
        next_page = response.get('next')

    return results


def use_read_replica_if_available(queryset):
    """
    If there is a database called 'read_replica', use that database for the queryset.
    """
    return queryset.using("read_replica") if "read_replica" in settings.DATABASES else queryset
