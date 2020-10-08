import os

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.defaults import page_not_found, server_error
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from rest_framework_swagger.views import get_swagger_view

from ecommerce.core import views as core_views
from ecommerce.core.url_utils import get_lms_dashboard_url
from ecommerce.core.views import LogoutView
from ecommerce.extensions.customer.app import EdxOAuth2LoginView
from ecommerce.extensions.payment.views.apple_pay import ApplePayMerchantDomainAssociationView
from ecommerce.extensions.urls import urlpatterns as extensions_patterns


def handler403(_):
    """Redirect unauthorized users to the LMS student dashboard.

    Removing URLs isn't the most elegant way to hide Oscar's front-end from
    public view. It would require revising templates and parts of the Oscar core
    which assume that these URLs exist. However, a clean way to, in effect,
    disable these URLs is to only make them available to users with staff
    permissions, the same protection used to guard the management dashboard from
    public access.

    This minimally invasive approach allows us to protect Oscar's front-end
    without sacrificing any internal functionality. Users not authorized to view
    Oscar's front-end are redirected to the LMS student dashboard, as one would
    usually be after signing into the LMS.
    """
    return redirect(get_lms_dashboard_url())


admin.autodiscover()
admin.site.site_header = _('E-Commerce Service Administration')
admin.site.site_title = admin.site.site_header

oauth2_urlpatterns = [  # pylint: disable=invalid-name
    url(r'^login/$', EdxOAuth2LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url('', include('social_django.urls', namespace='social')),
]

# NOTE 1: Add our logout override first to ensure it is registered by Django as the actual logout view.
# NOTE 2: These same patterns are used for rest_framework's browseable API authentication links.
AUTH_URLS = [url(r'^logout/$', LogoutView.as_view(), name='logout'), ] + oauth2_urlpatterns

WELL_KNOWN_URLS = [
    url(r'^.well-known/apple-developer-merchantid-domain-association.txt$',
        ApplePayMerchantDomainAssociationView.as_view(), name='apple_pay_domain_association'),
]

urlpatterns = AUTH_URLS + WELL_KNOWN_URLS + [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^auto_auth/$', core_views.AutoAuth.as_view(), name='auto_auth'),
    url(r'^api-auth/', include(AUTH_URLS, namespace='rest_framework')),
    url(r'^api-docs/', get_swagger_view(title='Ecommerce API'), name='api_docs'),
    url(r'^courses/', include('ecommerce.courses.urls', namespace='courses')),
    url(r'^credit/', include('ecommerce.credit.urls', namespace='credit')),
    url(r'^coupons/', include('ecommerce.coupons.urls', namespace='coupons')),
    url(r'^health/$', core_views.health, name='health'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(packages=['courses']), name='javascript-catalog'),
    url(r'^management/', include('ecommerce.management.urls', namespace='management')),
    url(r'^programs/', include('ecommerce.programs.urls', namespace='programs')),
    url(r'^enterprise/', include('ecommerce.enterprise.urls', namespace='enterprise')),
    url(r'^journals/', include('ecommerce.journals.urls', namespace='journals')),  # TODO: journals dependency
]

# Install Oscar extension URLs
urlpatterns += extensions_patterns

robots = TemplateView.as_view(template_name='robots.txt', content_type='text/plain')
urlpatterns += [
    url(r'^robots\.txt$', robots, name='robots')
]

if settings.DEBUG and settings.MEDIA_ROOT:  # pragma: no cover
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

if settings.DEBUG:  # pragma: no cover
    urlpatterns += [
        url(r'^403/$', handler403, name='403'),
        url(r'^404/$', page_not_found, name='404'),
        url(r'^500/$', server_error, name='500'),
        url(r'^bootstrap/$', TemplateView.as_view(template_name='bootstrap-demo.html')),
    ]
    # Allow error pages to be tested

    if os.environ.get('ENABLE_DJANGO_TOOLBAR', False):
        import debug_toolbar  # pylint: disable=import-error, wrong-import-position,wrong-import-order

        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls))
        ]
