import logging
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils.functional import lazy
from mozilla_django_oidc.utils import import_from_settings

logger = logging.getLogger(__name__)


class OidcDiscoveryError(Exception):
    pass


class OidcProvider:
    """The OpenID provider found under OIDC_ISSUER_URL.

    Its endpoints come from the discovery document the issuer publishes
    (OpenID Connect Discovery 1.0), so any compliant provider works with only
    its issuer URL, such as a Keycloak realm or an Entra ID tenant. Without an
    issuer URL, settings.py sets the endpoints of the Keycloak behind
    auth-<PROJECT_NAME> itself, and those are used as they are.
    """

    DISCOVERY_PATH = "/.well-known/openid-configuration"
    CACHE_TIMEOUT = 60 * 60
    REQUEST_TIMEOUT = 5
    # mozilla-django-oidc setting -> key in the discovery document
    ENDPOINT_KEYS = {
        "OIDC_OP_AUTHORIZATION_ENDPOINT": "authorization_endpoint",
        "OIDC_OP_TOKEN_ENDPOINT": "token_endpoint",
        "OIDC_OP_USER_ENDPOINT": "userinfo_endpoint",
        "OIDC_OP_JWKS_ENDPOINT": "jwks_uri",
        "OIDC_OP_LOGOUT": "end_session_endpoint",
    }

    def __init__(self, issuer_url: str):
        self.issuer_url = issuer_url

    @classmethod
    def get_settings(cls, attr: str, *args: Any) -> Any:
        """mozilla-django-oidc's get_settings(), with discovered endpoints.

        Its backend reads the endpoints when it is created, which Django does
        for every authentication and for every request of a user logged in
        through it. An endpoint is therefore only looked up once it is used, so
        those requests do not depend on the provider being reachable.
        """
        if cls._is_discovered(attr):
            return lazy(cls.discovered_endpoint, str)(attr)
        return import_from_settings(attr, *args)

    @classmethod
    def discovered_endpoint(cls, attr: str) -> str:
        endpoint = cls(settings.OIDC_ISSUER_URL).endpoint(cls.ENDPOINT_KEYS[attr])
        if endpoint is None:
            raise OidcDiscoveryError(
                f"{settings.OIDC_ISSUER_URL} publishes no {cls.ENDPOINT_KEYS[attr]}"
            )
        return endpoint

    @classmethod
    def logout_url(cls) -> str | None:
        """Where to end the session at the provider; None if it has no such page.

        Also None if the provider cannot be reached: logging out of montrek
        must not depend on it.
        """
        if not cls._is_discovered("OIDC_OP_LOGOUT"):
            return getattr(settings, "OIDC_OP_LOGOUT", None)
        try:
            return cls(settings.OIDC_ISSUER_URL).endpoint("end_session_endpoint")
        except OidcDiscoveryError:
            return None

    @classmethod
    def _is_discovered(cls, attr: str) -> bool:
        return (
            attr in cls.ENDPOINT_KEYS
            and bool(settings.OIDC_ISSUER_URL)
            and getattr(settings, attr, None) is None
        )

    def endpoint(self, key: str) -> str | None:
        return self.configuration().get(key)

    def configuration(self) -> dict[str, Any]:
        cache_key = f"montrek-oidc-configuration:{self.issuer_url}"
        configuration = cache.get(cache_key)
        if configuration is None:
            configuration = self._fetch_configuration()
            cache.set(cache_key, configuration, self.CACHE_TIMEOUT)
        return configuration

    def _fetch_configuration(self) -> dict[str, Any]:
        url = self.issuer_url.rstrip("/") + self.DISCOVERY_PATH
        try:
            response = requests.get(
                url,
                timeout=self.REQUEST_TIMEOUT,
                **getattr(settings, "OIDC_EXTRA_REQUEST_ARGS", {}),
            )
            response.raise_for_status()
            configuration = response.json()
        except (requests.RequestException, ValueError) as error:
            logger.exception("OIDC discovery at %s failed", url)
            raise OidcDiscoveryError(f"OIDC discovery at {url} failed") from error
        # Required by the spec: a document naming another issuer may belong to
        # a different provider, and tokens would be checked against its keys.
        if configuration.get("issuer") != self.issuer_url:
            raise OidcDiscoveryError(
                f"{url} names issuer {configuration.get('issuer')!r}, "
                f"not {self.issuer_url!r}"
            )
        return configuration
