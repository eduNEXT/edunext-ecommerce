from __future__ import absolute_import

from path import Path

from ecommerce.settings.base import *


SITE_ID = 1

# TEST SETTINGS
INSTALLED_APPS += (
    'django_nose',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

LOGGING['handlers']['local'] = {'class': 'logging.NullHandler'}

if os.getenv('DISABLE_MIGRATIONS'):

    class DisableMigrations(object):

        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return "notmigrations"


    MIGRATION_MODULES = DisableMigrations()
# END TEST SETTINGS


# IN-MEMORY TEST DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'ATOMIC_REQUESTS': True,
    },
}
# END IN-MEMORY TEST DATABASE


# AUTHENTICATION
ENABLE_AUTO_AUTH = True

JWT_AUTH.update({
    'JWT_SECRET_KEY': 'insecure-secret-key',
    'JWT_ISSUERS': ('test-issuer',),
})

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
# END AUTHENTICATION


# ORDER PROCESSING
EDX_API_KEY = 'replace-me'
# END ORDER PROCESSING


# PAYMENT PROCESSING
PAYMENT_PROCESSOR_CONFIG = {
    'edx': {
        'cybersource': {
            'soap_api_url': 'https://ics2wstest.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.115.wsdl',
            'merchant_id': 'fake-merchant-id',
            'transaction_key': 'fake-transaction-key',
            'profile_id': 'fake-profile-id',
            'access_key': 'fake-access-key',
            'secret_key': 'fake-secret-key',
            'payment_page_url': 'https://replace-me/',
            'receipt_path': PAYMENT_PROCESSOR_RECEIPT_PATH,
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'send_level_2_3_details': True,
            'sop_profile_id': 'sop-fake-profile-id',
            'sop_access_key': 'sop-fake-access-key',
            'sop_secret_key': 'sop-fake-secret-key',
            'sop_payment_page_url': 'https://sop-replace-me/',
        },
        'paypal': {
            'mode': 'sandbox',
            'client_id': 'fake-client-id',
            'client_secret': 'fake-client-secret',
            'receipt_path': PAYMENT_PROCESSOR_RECEIPT_PATH,
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'error_path': PAYMENT_PROCESSOR_ERROR_PATH,
        },
        'payu': {
            'payment_page_url': 'https://sandbox.gateway.payulatam.com/ppp-web-gateway',
            'response_url': 'fake-response-url',
            'confirmation_url': 'fake-confirmation-url',
            'merchant_id': '123456',
            'account_id': '123456',
            'api_key': 'fake-api-key',
            'tax': '0',
            'tax_return_base': '0',
            'test': '1',
        },
        'invoice': {}
    },
    'other': {
        'cybersource': {
            'soap_api_url': 'https://ics2wstest.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.115.wsdl',
            'merchant_id': 'other-fake-merchant-id',
            'transaction_key': 'other-fake-transaction-key',
            'profile_id': 'other-fake-profile-id',
            'access_key': 'other-fake-access-key',
            'secret_key': 'other-fake-secret-key',
            'payment_page_url': 'https://replace-me/',
            'receipt_path': PAYMENT_PROCESSOR_RECEIPT_PATH,
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'send_level_2_3_details': True,
        },
        'paypal': {
            'mode': 'sandbox',
            'client_id': 'pther-fake-client-id',
            'client_secret': 'pther-fake-client-secret',
            'receipt_path': PAYMENT_PROCESSOR_RECEIPT_PATH,
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'error_path': PAYMENT_PROCESSOR_ERROR_PATH,
        },
        'payu': {
            'payment_page_url': 'https://sandbox.gateway.payulatam.com/ppp-web-gateway',
            'response_url': 'fake-response-url',
            'confirmation_url': 'fake-confirmation-url',
            'merchant_id': '123456',
            'account_id': '123456',
            'api_key': 'fake-api-key',
            'tax': '0',
            'tax_return_base': '0',
            'test': '1',
        },
        'invoice': {}
    }
}

# END PAYMENT PROCESSING


# CELERY
# Run tasks in-process, without sending them to the queue (i.e., synchronously).
CELERY_ALWAYS_EAGER = True
# END CELERY


# Use production settings for asset compression so that asset compilation can be tested on the CI server.
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

# Comprehensive theme settings for testing environment
COMPREHENSIVE_THEME_DIRS = [
    Path(DJANGO_ROOT + "/tests/themes"),
    Path(DJANGO_ROOT + "/tests/themes-dir-2"),
]

DEFAULT_SITE_THEME = "test-theme"
