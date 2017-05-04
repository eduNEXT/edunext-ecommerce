""" Payment-related URLs """
from django.conf.urls import url

from ecommerce.extensions.payment.views import cybersource, PaymentFailedView
from ecommerce.extensions.payment.views.paypal import PaypalPaymentExecutionView, PaypalProfileAdminView
from ecommerce.extensions.payment.views.payu import PayUPaymentResponseView

urlpatterns = [
    url(r'^cybersource/notify/$', cybersource.CybersourceNotifyView.as_view(), name='cybersource_notify'),
    url(r'^cybersource/redirect/$', cybersource.CybersourceInterstitialView.as_view(), name='cybersource_redirect'),
    url(r'^cybersource/submit/$', cybersource.CybersourceSubmitView.as_view(), name='cybersource_submit'),
    url(r'^error/$', PaymentFailedView.as_view(), name='payment_error'),
    url(r'^paypal/execute/$', PaypalPaymentExecutionView.as_view(), name='paypal_execute'),
    url(r'^paypal/profiles/$', PaypalProfileAdminView.as_view(), name='paypal_profiles'),
    url(r'^payu/notify/$', PayUPaymentResponseView.as_view(), name='payu_notify'),
]
