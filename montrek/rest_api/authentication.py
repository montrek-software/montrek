from django.conf import settings
from rest_framework import authentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class MontrekApiAuthentication(authentication.BaseAuthentication):
    """
    Accepts a Bearer token issued either by montrek itself (SimpleJWT, via
    /rest_api/token/) or, when Keycloak is enabled, by Keycloak.

    Users logging in through Keycloak have no usable Django password, so they
    cannot obtain a SimpleJWT token. They request an access token from
    Keycloak instead, which is validated against Keycloak's userinfo endpoint.
    """

    www_authenticate_realm = "api"

    def authenticate(self, request):
        try:
            return JWTAuthentication().authenticate(request)
        except InvalidToken:
            # Not a montrek token - it may still be one issued by Keycloak.
            if not settings.ENABLE_KEYCLOAK:
                raise
            return self.authenticate_with_keycloak(request)

    def authenticate_with_keycloak(self, request):
        # Imported here: the OIDC backend only exists when Keycloak is enabled.
        from mozilla_django_oidc.contrib.drf import OIDCAuthentication

        return OIDCAuthentication().authenticate(request)

    def authenticate_header(self, request):
        return f'Bearer realm="{self.www_authenticate_realm}"'
