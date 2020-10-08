from django.conf.urls import include, url
from ecommerce.core.views import LogoutView
from ecommerce.extensions.customer.app import EdxOAuth2LoginView
from oscar.apps.dashboard import app
from oscar.core.loading import get_class

oauth2_urlpatterns = [  # pylint: disable=invalid-name
    url(r'^login/$', EdxOAuth2LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url('', include('social_django.urls', namespace='social')),
]

# Note: Add ecommerce's logout override first to ensure it is registered by Django as the
# actual logout view. Ecommerce's logout implementation supports different site configuration.
AUTH_URLS = [url(r'^logout/$', LogoutView.as_view(), name='logout'), ] + oauth2_urlpatterns


class DashboardApplication(app.DashboardApplication):
    index_view = get_class('dashboard.views', 'ExtendedIndexView')
    refunds_app = get_class('dashboard.refunds.app', 'application')

    def get_urls(self):
        urls = [
            url(r'^$', self.index_view.as_view(), name='index'),
            url(r'^catalogue/', include(self.catalogue_app.urls)),
            url(r'^reports/', include(self.reports_app.urls)),
            url(r'^orders/', include(self.orders_app.urls)),
            url(r'^users/', include(self.users_app.urls)),
            url(r'^content-blocks/', include(self.promotions_app.urls)),
            url(r'^pages/', include(self.pages_app.urls)),
            url(r'^partners/', include(self.partners_app.urls)),
            url(r'^offers/', include(self.offers_app.urls)),
            url(r'^ranges/', include(self.ranges_app.urls)),
            url(r'^reviews/', include(self.reviews_app.urls)),
            url(r'^vouchers/', include(self.vouchers_app.urls)),
            url(r'^comms/', include(self.comms_app.urls)),
            url(r'^shipping/', include(self.shipping_app.urls)),
            url(r'^refunds/', include(self.refunds_app.urls)),
        ]
        urls += AUTH_URLS
        return self.post_process_urls(urls)


application = DashboardApplication()
