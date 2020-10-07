from auth_backends.views import LoginRedirectBaseView
from crum import get_current_request
from ecommerce.core.views import LogoutView
from oscar.apps.customer import app


class EdxOAuth2LoginView(LoginRedirectBaseView):

    @property
    def auth_backend_name(self):
        request = get_current_request()
        if request.site.siteconfiguration.oauth_settings.get('BACKEND_SERVICE_EDX_OAUTH2_KEY'):
            return 'edx-oauth2'

        return 'edx-oidc'


class CustomerApplication(app.CustomerApplication):
    login_view = EdxOAuth2LoginView
    logout_view = LogoutView


application = CustomerApplication()
