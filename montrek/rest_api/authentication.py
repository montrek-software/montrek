import logging

from django.conf import settings
from rest_framework import authentication, exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from user.modules.oidc_provider import OidcProvider
from user.repositories.user_repository import MontrekUserRepository

from rest_api.modules.provider_access_token import (
    ProviderAccessToken,
    ProviderTokenError,
)

logger = logging.getLogger(__name__)


class MontrekApiAuthentication(authentication.BaseAuthentication):
    """
    Accepts a Bearer token issued either by montrek itself (SimpleJWT, via
    /rest_api/token/) or, when OIDC login is enabled, by the OpenID provider,
    such as Keycloak.

    Users logging in through the provider have no usable Django password, so
    they cannot obtain a SimpleJWT token. They request an access token from the
    provider instead. With OIDC_API_AUDIENCE, montrek checks it itself
    (ProviderAccessToken) and maps its subject to the user linked to it;
    without, it is validated against the provider's userinfo endpoint.
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
        if settings.OIDC_API_AUDIENCE:
            return self.authenticate_with_provider_token(request)
        return self.authenticate_with_userinfo(request)

    def authenticate_with_provider_token(self, request):
        jwt_authentication = JWTAuthentication()
        token = jwt_authentication.get_raw_token(jwt_authentication.get_header(request))
        try:
            claims = ProviderAccessToken(token.decode()).claims()
        except ProviderTokenError as error:
            logger.info("Provider token refused: %s", error)
            raise exceptions.AuthenticationFailed("Invalid token.") from error
        # A person who has signed in through the browser once, or an
        # application whose subject an admin has entered for its montrek user.
        user = (
            MontrekUserRepository()
            .with_oidc_subject(OidcProvider.issuer(), claims["sub"])
            .first()
        )
        if user is None:
            raise exceptions.AuthenticationFailed(
                "No montrek user is linked to the token's subject."
            )
        if not user.is_active:
            raise exceptions.AuthenticationFailed("User is inactive.")
        return user, token.decode()

    def authenticate_with_userinfo(self, request):
        # Imported here: the OIDC backend only exists when OIDC is enabled.
        from mozilla_django_oidc.contrib.drf import OIDCAuthentication

        result = OIDCAuthentication().authenticate(request)
        # The library checks only that the user exists. A user deactivated in
        # montrek may still be active at the provider and hold a valid token.
        if result is not None and not result[0].is_active:
            raise exceptions.AuthenticationFailed("User is inactive.")
        return result

    def authenticate_header(self, request):
        return f'Bearer realm="{self.www_authenticate_realm}"'
