import ssl
from typing import Any, ClassVar

import jwt
from django.conf import settings
from user.modules.oidc_provider import OidcProvider


class ProviderTokenError(Exception):
    pass


class ProviderAccessToken:
    """An access token the OpenID provider issued for montrek's API, checked
    here: its signature against the provider's published keys, its issuer, its
    audience (OIDC_API_AUDIENCE), its expiry, and a scope or app role
    (OIDC_API_SCOPE).

    The provider's userinfo endpoint answers for any of the user's tokens,
    whatever app it was issued to; with Entra ID it is Microsoft Graph, which
    accepts a Graph token any app of the tenant obtained for the user. Only
    the audience shows that a token is meant for montrek.
    """

    ALGORITHMS = ["RS256"]
    LEEWAY_SECONDS = 30
    JWKS_TIMEOUT_SECONDS = 5
    # One per URI, kept for the process: each caches the provider's keys and
    # fetches them again only for a key ID it does not know.
    _jwks_clients: ClassVar[dict[str, jwt.PyJWKClient]] = {}

    def __init__(self, token: str):
        self.token = token

    def claims(self) -> dict[str, Any]:
        try:
            key = self.jwks_client().get_signing_key_from_jwt(self.token)
            claims = jwt.decode(
                self.token,
                key,
                algorithms=self.ALGORITHMS,
                audience=settings.OIDC_API_AUDIENCE,
                issuer=OidcProvider.issuer(),
                leeway=self.LEEWAY_SECONDS,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except jwt.PyJWTError as error:
            raise ProviderTokenError(str(error)) from error
        scope = settings.OIDC_API_SCOPE
        # Without a scope to require, every token for the audience would do:
        # with Entra ID, any app of the tenant can get one by client
        # credentials. settings.py refuses that configuration; this keeps it
        # closed should it get here anyway.
        if not scope or scope not in self.granted(claims):
            raise ProviderTokenError(f"The token does not grant {scope!r}.")
        return claims

    @staticmethod
    def granted(claims: dict[str, Any]) -> set[str]:
        """Scopes a user delegated (scp in Entra ID, scope in RFC 9068 and
        Keycloak, space-separated) and app roles an application holds (roles)."""
        granted: set[str] = set()
        for claim in ("scp", "scope"):
            if isinstance(value := claims.get(claim), str):
                granted.update(value.split())
        if isinstance(roles := claims.get("roles"), list):
            granted.update(role for role in roles if isinstance(role, str))
        return granted

    @classmethod
    def jwks_client(cls) -> jwt.PyJWKClient:
        uri = str(OidcProvider.get_settings("OIDC_OP_JWKS_ENDPOINT"))
        if uri not in cls._jwks_clients:
            cls._jwks_clients[uri] = jwt.PyJWKClient(
                uri,
                cache_keys=True,
                timeout=cls.JWKS_TIMEOUT_SECONDS,
                # The bundle the other provider requests use, which holds the
                # instance CA where there is one.
                ssl_context=cls.ssl_context(),
            )
        return cls._jwks_clients[uri]

    @staticmethod
    def ssl_context() -> ssl.SSLContext:
        context = ssl.create_default_context(
            cafile=getattr(settings, "CA_BUNDLE", None)
        )
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        # The defaults already, stated so that no later change loosens them.
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        return context
