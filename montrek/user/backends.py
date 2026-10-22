from typing import Any

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from user.modules.oidc_provider import OidcProvider


class MontrekOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    get_settings = staticmethod(OidcProvider.get_settings)

    def verify_token(self, token: Any, **kwargs: Any) -> dict[str, Any]:
        payload = super().verify_token(token, **kwargs)
        # mozilla-django-oidc checks the signature, not who issued the token.
        # With an issuer URL configured, only that issuer's tokens count.
        issuer = settings.OIDC_ISSUER_URL
        if issuer and payload.get("iss") != issuer:
            raise SuspiciousOperation("ID token from another issuer")
        return payload
