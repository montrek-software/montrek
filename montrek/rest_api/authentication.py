from django.conf import settings
from rest_framework import authentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class MontrekApiAuthentication(authentication.BaseAuthentication):
    """
    Accepts a Bearer token issued either by montrek itself (SimpleJWT, via
    /rest_api/token/) or, when OIDC login is enabled, by the OpenID provider,
    such as Keycloak.

    Users logging in through the provider have no usable Django password, so
    they cannot obtain a SimpleJWT token. They request an access token from the
    provider instead, which is validated against its userinfo endpoint.
    """

    www_authenticate_realm = "api"

    def authenticate(self, request):
        try:
            return JWTAuthentication().authenticate(request)
        except InvalidToken:
            # Not a montrek token - it may still be one issued by the provider.
            if not settings.ENABLE_OIDC:
                raise
            return self.authenticate_with_oidc(request)

    def authenticate_with_oidc(self, request):
        # Imported here: the OIDC backend only exists when OIDC is enabled.
        from mozilla_django_oidc.contrib.drf import OIDCAuthentication

        return OIDCAuthentication().authenticate(request)

    def authenticate_header(self, request):
        return f'Bearer realm="{self.www_authenticate_realm}"'
