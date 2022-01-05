"""Oscar-specific settings"""


from django.utils.translation import ugettext_lazy as _
from oscar.defaults import *

from ecommerce.extensions.fulfillment.status import LINE, ORDER
from ecommerce.extensions.refund.status import REFUND, REFUND_LINE

# URL CONFIGURATION
OSCAR_HOMEPAGE = reverse_lazy('dashboard:index')
# END URL CONFIGURATION


# APP CONFIGURATION
OSCAR_APPS = [
    'oscar',
    'oscar.apps.address',
    'oscar.apps.shipping',
    'oscar.apps.catalogue.reviews',
    'oscar.apps.search',
    'oscar.apps.wishlists',

    'ecommerce.extensions',
    'ecommerce.extensions.api',
    'ecommerce.extensions.fulfillment',
    'ecommerce.extensions.refund',
    'ecommerce.extensions.analytics',
    'ecommerce.extensions.basket',
    'ecommerce.extensions.catalogue',
    'ecommerce.extensions.checkout',
    'ecommerce.extensions.customer',
    'ecommerce.extensions.offer',
    'ecommerce.extensions.order',
    'ecommerce.extensions.partner',
    'ecommerce.extensions.payment',
    'ecommerce.extensions.voucher',

    'oscar.apps.dashboard.reports',
    'oscar.apps.dashboard.catalogue',
    'oscar.apps.dashboard.partners',
    'oscar.apps.dashboard.pages',
    'oscar.apps.dashboard.ranges',
    'oscar.apps.dashboard.reviews',
    'oscar.apps.dashboard.vouchers',
    'oscar.apps.dashboard.communications',
    'oscar.apps.dashboard.shipping',

    'ecommerce.extensions.dashboard',
    'ecommerce.extensions.dashboard.offers',
    'ecommerce.extensions.dashboard.refunds',
    'ecommerce.extensions.dashboard.orders',
    'ecommerce.extensions.dashboard.users',

    # 3rd-party apps that oscar depends on
    'haystack',
    'treebeard',
    'django_tables2',
    'sorl.thumbnail',
]
# END APP CONFIGURATION


# ORDER PROCESSING

# The initial status for an order, or an order line.
OSCAR_INITIAL_ORDER_STATUS = ORDER.OPEN
OSCAR_INITIAL_LINE_STATUS = LINE.OPEN

# This dict defines the new order statuses than an order can move to
OSCAR_ORDER_STATUS_PIPELINE = {
    ORDER.PENDING: (ORDER.OPEN, ORDER.PAYMENT_ERROR),
    ORDER.PAYMENT_ERROR: (),
    ORDER.OPEN: (ORDER.COMPLETE, ORDER.FULFILLMENT_ERROR),
    ORDER.FULFILLMENT_ERROR: (ORDER.COMPLETE,),
    ORDER.COMPLETE: ()
}

# This is a dict defining all the statuses a single line in an order may have.
OSCAR_LINE_STATUS_PIPELINE = {
    LINE.OPEN: (
        LINE.COMPLETE,
        LINE.FULFILLMENT_CONFIGURATION_ERROR,
        LINE.FULFILLMENT_NETWORK_ERROR,
        LINE.FULFILLMENT_TIMEOUT_ERROR,
        LINE.FULFILLMENT_SERVER_ERROR,
    ),
    LINE.FULFILLMENT_CONFIGURATION_ERROR: (LINE.COMPLETE,),
    LINE.FULFILLMENT_NETWORK_ERROR: (LINE.COMPLETE,),
    LINE.FULFILLMENT_TIMEOUT_ERROR: (LINE.COMPLETE,),
    LINE.FULFILLMENT_SERVER_ERROR: (LINE.COMPLETE,),
    LINE.COMPLETE: (),
}

# This dict defines the line statuses that will be set when an order's status is changed
OSCAR_ORDER_STATUS_CASCADE = {
    ORDER.OPEN: LINE.OPEN,
}

# Fulfillment Modules allows specific fulfillment modules to be evaluated in a specific order.
# Each fulfillment module supports handling a certain set of Product Types, and will evaluate the
# lines in the order to determine which it can fulfill.
FULFILLMENT_MODULES = [
    'ecommerce.extensions.fulfillment.modules.EnrollmentFulfillmentModule',
    'ecommerce.extensions.fulfillment.modules.CouponFulfillmentModule',
    'ecommerce.extensions.fulfillment.modules.EnrollmentCodeFulfillmentModule',
    'ecommerce.extensions.fulfillment.modules.CourseEntitlementFulfillmentModule',
    'ecommerce.extensions.fulfillment.modules.DonationsFromCheckoutTestFulfillmentModule',
]

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

AUTHENTICATION_BACKENDS = (
    'rules.permissions.ObjectPermissionBackend',
    'oscar.apps.customer.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

OSCAR_DEFAULT_CURRENCY = 'USD'
# END ORDER PROCESSING


# PAYMENT PROCESSING
PAYMENT_PROCESSORS = (
    'ecommerce.extensions.payment.processors.cybersource.Cybersource',
    'ecommerce.extensions.payment.processors.cybersource.CybersourceREST',
    'ecommerce.extensions.payment.processors.paypal.Paypal',
    'ecommerce.extensions.payment.processors.stripe.Stripe',
)

PAYMENT_PROCESSOR_RECEIPT_PATH = '/checkout/receipt/'
PAYMENT_PROCESSOR_CANCEL_PATH = '/checkout/cancel-checkout/'
PAYMENT_PROCESSOR_ERROR_PATH = '/checkout/error/'

PAYMENT_PROCESSOR_CONFIG = {
    'edx': {
        'cybersource': {
            'profile_id': None,
            'access_key': None,
            'secret_key': None,
            'payment_page_url': None,
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'send_level_2_3_details': True,
            'apple_pay_merchant_identifier': '',
            'apple_pay_merchant_id_domain_association': '',
            'apple_pay_merchant_id_certificate_path': '',
            'apple_pay_country_code': '',
        },
        'cybersource-rest': {
            'profile_id': None,
            'access_key': None,
            'secret_key': None,
            'payment_page_url': None,
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'send_level_2_3_details': True,
            'apple_pay_merchant_identifier': '',
            'apple_pay_merchant_id_domain_association': '',
            'apple_pay_merchant_id_certificate_path': '',
            'apple_pay_country_code': '',
        },
        'paypal': {
            # 'mode' can be either 'sandbox' or 'live'
            'mode': None,
            'client_id': None,
            'client_secret': None,
            'cancel_checkout_path': PAYMENT_PROCESSOR_CANCEL_PATH,
            'error_path': PAYMENT_PROCESSOR_ERROR_PATH,
        },
        'stripe': {
            'publishable_key': None,
            'secret_key': None,
            'country': None,
            'apple_pay_merchant_id_domain_association': '7B227073704964223A2239373943394538343346343131343044463144313834343232393232313734313034353044314339464446394437384337313531303944334643463542433731222C2276657273696F6E223A312C22637265617465644F6E223A313437313435343137313137362C227369676E6174757265223A2233303830303630393261383634383836663730643031303730326130383033303830303230313031333130663330306430363039363038363438303136353033303430323031303530303330383030363039326138363438383666373064303130373031303030306130383033303832303365363330383230333862613030333032303130323032303836383630663639396439636361373066333030613036303832613836343863653364303430333032333037613331326533303263303630333535303430333063323534313730373036633635323034313730373036633639363336313734363936663665323034393665373436353637373236313734363936663665323034333431323032643230343733333331323633303234303630333535303430623063316434313730373036633635323034333635373237343639363636393633363137343639366636653230343137353734363836663732363937343739333131333330313130363033353530343061306330613431373037303663363532303439366536333265333130623330303930363033353530343036313330323535353333303165313730643331333633303336333033333331333833313336333433303561313730643332333133303336333033323331333833313336333433303561333036323331323833303236303630333535303430333063316636353633363332643733366437303264363237323666366236353732326437333639363736653566353534333334326435333431346534343432346635383331313433303132303630333535303430623063306236393466353332303533373937333734363536643733333131333330313130363033353530343061306330613431373037303663363532303439366536333265333130623330303930363033353530343036313330323535353333303539333031333036303732613836343863653364303230313036303832613836343863653364303330313037303334323030303438323330666461626333396366373565323032633530643939623435313265363337653261393031646436636233653062316364346235323637393866386366346562646538316132356138633231653463333364646365386532613936633266366166613139333033343563346538376134343236636539353162313239356133383230323131333038323032306433303435303630383262303630313035303530373031303130343339333033373330333530363038326230363031303530353037333030313836323936383734373437303361326632663666363337333730326536313730373036633635326536333666366432663666363337333730333033343264363137303730366336353631363936333631333333303332333031643036303335353164306530343136303431343032323433303062396165656564343633313937613461363561323939653432373138323163343533303063303630333535316431333031303166663034303233303030333031663036303335353164323330343138333031363830313432336632343963343466393365346566323765366334663632383663336661326262666432653462333038323031316430363033353531643230303438323031313433303832303131303330383230313063303630393261383634383836663736333634303530313330383166653330383163333036303832623036303130353035303730323032333038316236306338316233353236353663363936313665363336353230366636653230373436383639373332303633363537323734363936363639363336313734363532303632373932303631366537393230373036313732373437393230363137333733373536643635373332303631363336333635373037343631366536333635323036663636323037343638363532303734363836353665323036313730373036633639363336313632366336353230373337343631366536343631373236343230373436353732366437333230363136653634323036333666366536343639373436393666366537333230366636363230373537333635326332303633363537323734363936363639363336313734363532303730366636633639363337393230363136653634323036333635373237343639363636393633363137343639366636653230373037323631363337343639363336353230373337343631373436353664363536653734373332653330333630363038326230363031303530353037303230313136326136383734373437303361326632663737373737373265363137303730366336353265363336663664326636333635373237343639363636393633363137343635363137353734363836663732363937343739326633303334303630333535316431663034326433303262333032396130323761303235383632333638373437343730336132663266363337323663326536313730373036633635326536333666366432663631373037303663363536313639363336313333326536333732366333303065303630333535316430663031303166663034303430333032303738303330306630363039326138363438383666373633363430363164303430323035303033303061303630383261383634386365336430343033303230333439303033303436303232313030646131633633616538626535663634663865313165383635363933376239623639633437326265393365616333323333613136373933366534613864356538333032323130306264356166626638363966336330636132373462326664646534663731373135396362336264373139396232636130666634303964653635396138326232346433303832303265653330383230323735613030333032303130323032303834393664326662663361393864613937333030613036303832613836343863653364303430333032333036373331316233303139303630333535303430333063313234313730373036633635323035323666366637343230343334313230326432303437333333313236333032343036303335353034306230633164343137303730366336353230343336353732373436393636363936333631373436393666366532303431373537343638366637323639373437393331313333303131303630333535303430613063306134313730373036633635323034393665363332653331306233303039303630333535303430363133303235353533333031653137306433313334333033353330333633323333333433363333333035613137306433323339333033353330333633323333333433363333333035613330376133313265333032633036303335353034303330633235343137303730366336353230343137303730366336393633363137343639366636653230343936653734363536373732363137343639366636653230343334313230326432303437333333313236333032343036303335353034306230633164343137303730366336353230343336353732373436393636363936333631373436393666366532303431373537343638366637323639373437393331313333303131303630333535303430613063306134313730373036633635323034393665363332653331306233303039303630333535303430363133303235353533333035393330313330363037326138363438636533643032303130363038326138363438636533643033303130373033343230303034663031373131383431396437363438356435316135653235383130373736653838306132656664653762616534646530386466633462393365313333353664353636356233356165323264303937373630643232346537626261303866643736313763653838636237366262363637306265633865383239383466663534343561333831663733303831663433303436303630383262303630313035303530373031303130343361333033383330333630363038326230363031303530353037333030313836326136383734373437303361326632663666363337333730326536313730373036633635326536333666366432663666363337333730333033343264363137303730366336353732366636663734363336313637333333303164303630333535316430653034313630343134323366323439633434663933653465663237653663346636323836633366613262626664326534623330306630363033353531643133303130316666303430353330303330313031666633303166303630333535316432333034313833303136383031346262623064656131353833333838396161343861393964656265626465626166646163623234616233303337303630333535316431663034333033303265333032636130326161303238383632363638373437343730336132663266363337323663326536313730373036633635326536333666366432663631373037303663363537323666366637343633363136373333326536333732366333303065303630333535316430663031303166663034303430333032303130363330313030363061326138363438383666373633363430363032306530343032303530303330306130363038326138363438636533643034303330323033363730303330363430323330336163663732383335313136393962313836666233356333353663613632626666343137656464393066373534646132386562656631396338313565343262373839663839386637396235393966393864353431306438663964653963326665303233303332326464353434323162306133303537373663356466333338336239303637666431373763326332313664393634666336373236393832313236663534663837613764316239396362396230393839323136313036393930663039393231643030303033313832303136303330383230313563303230313031333038313836333037613331326533303263303630333535303430333063323534313730373036633635323034313730373036633639363336313734363936663665323034393665373436353637373236313734363936663665323034333431323032643230343733333331323633303234303630333535303430623063316434313730373036633635323034333635373237343639363636393633363137343639366636653230343137353734363836663732363937343739333131333330313130363033353530343061306330613431373037303663363532303439366536333265333130623330303930363033353530343036313330323535353330323038363836306636393964396363613730663330306430363039363038363438303136353033303430323031303530306130363933303138303630393261383634383836663730643031303930333331306230363039326138363438383666373064303130373031333031633036303932613836343838366637306430313039303533313066313730643331333633303338333133373331333733313336333133313561333032663036303932613836343838366637306430313039303433313232303432303733343832623432653665366332323264616536643963303961346336663332316534656136653666326661626631356430376562333338643264613435646233303061303630383261383634386365336430343033303230343438333034363032323130306564333264376438616131623536623036626164623162396639396264643063653662363931316530623032393232633934333362663564326130656135353830323231303066393433353637663030323361643061343561373236663238376636303062656334666566373335383832383935633733313531383337336163383934383137303030303030303030303030227D',
        },
    },
}

PAYMENT_PROCESSOR_SWITCH_PREFIX = 'payment_processor_active_'
# END PAYMENT PROCESSING


# ANALYTICS
# Here Be Dragons: Use this feature flag to control whether Oscar should install its
# default analytics receivers. This is disabled by default. Some default receivers,
# such as the receiver responsible for tallying product orders, make row-locking
# queries which significantly degrade performance at scale.
INSTALL_DEFAULT_ANALYTICS_RECEIVERS = False
# END ANALYTICS


# REFUND PROCESSING
OSCAR_INITIAL_REFUND_STATUS = REFUND.OPEN
OSCAR_INITIAL_REFUND_LINE_STATUS = REFUND_LINE.OPEN

OSCAR_REFUND_STATUS_PIPELINE = {
    REFUND.OPEN: (REFUND.DENIED, REFUND.PAYMENT_REFUND_ERROR, REFUND.PAYMENT_REFUNDED),
    REFUND.PAYMENT_REFUND_ERROR: (REFUND.PAYMENT_REFUNDED, REFUND.PAYMENT_REFUND_ERROR),
    REFUND.PAYMENT_REFUNDED: (REFUND.REVOCATION_ERROR, REFUND.COMPLETE),
    REFUND.REVOCATION_ERROR: (REFUND.REVOCATION_ERROR, REFUND.COMPLETE),
    REFUND.DENIED: (),
    REFUND.COMPLETE: ()
}

OSCAR_REFUND_LINE_STATUS_PIPELINE = {
    REFUND_LINE.OPEN: (REFUND_LINE.DENIED, REFUND_LINE.REVOCATION_ERROR, REFUND_LINE.COMPLETE),
    REFUND_LINE.REVOCATION_ERROR: (REFUND_LINE.REVOCATION_ERROR, REFUND_LINE.COMPLETE),
    REFUND_LINE.DENIED: (),
    REFUND_LINE.COMPLETE: ()
}
# END REFUND PROCESSING

# DASHBOARD NAVIGATION MENU
OSCAR_DASHBOARD_NAVIGATION = [
    {
        'label': _('Dashboard'),
        'icon': 'icon-th-list',
        'url_name': 'dashboard:index',
    },
    {
        'label': _('Catalogue'),
        'icon': 'icon-sitemap',
        'children': [
            {
                'label': _('Products'),
                'url_name': 'dashboard:catalogue-product-list',
            },
            {
                'label': _('Product Types'),
                'url_name': 'dashboard:catalogue-class-list',
            },
            {
                'label': _('Categories'),
                'url_name': 'dashboard:catalogue-category-list',
            },
            {
                'label': _('Ranges'),
                'url_name': 'dashboard:range-list',
            },
            {
                'label': _('Low stock alerts'),
                'url_name': 'dashboard:stock-alert-list',
            },
        ]
    },
    {
        'label': _('Fulfillment'),
        'icon': 'icon-shopping-cart',
        'children': [
            {
                'label': _('Orders'),
                'url_name': 'dashboard:order-list',
            },
            {
                'label': _('Statistics'),
                'url_name': 'dashboard:order-stats',
            },
            {
                'label': _('Partners'),
                'url_name': 'dashboard:partner-list',
            },
            {
                'label': _('Refunds'),
                'url_name': 'dashboard:refunds-list',
            },
        ]
    },
    {
        'label': _('Customers'),
        'icon': 'icon-group',
        'children': [
            {
                'label': _('Customers'),
                'url_name': 'dashboard:users-index',
            },
            {
                'label': _('Stock alert requests'),
                'url_name': 'dashboard:user-alert-list',
            },
        ]
    },
    {
        'label': _('Offers'),
        'icon': 'icon-bullhorn',
        'children': [
            {
                'label': _('Offers'),
                'url_name': 'dashboard:offer-list',
            },
            {
                'label': _('Vouchers'),
                'url_name': 'dashboard:voucher-list',
            },
        ],
    },
    {
        'label': _('Reports'),
        'icon': 'icon-bar-chart',
        'url_name': 'dashboard:reports-index',
    },
]
# END DASHBOARD NAVIGATION MENU

# Default timeout for Enrollment API calls
ENROLLMENT_FULFILLMENT_TIMEOUT = 7

# Coupon code length
VOUCHER_CODE_LENGTH = 16

THUMBNAIL_DEBUG = False

OSCAR_FROM_EMAIL = 'testing@example.com'
