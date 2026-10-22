from unittest import mock

import requests

ISSUER_URL = "https://login.example.com/tenant/v2.0"
DISCOVERY_URL = ISSUER_URL + "/.well-known/openid-configuration"
DISCOVERY_DOCUMENT = {
    "issuer": ISSUER_URL,
    "authorization_endpoint": "https://login.example.com/tenant/authorize",
    "token_endpoint": "https://login.example.com/tenant/token",
    "userinfo_endpoint": "https://login.example.com/userinfo",
    "jwks_uri": "https://login.example.com/tenant/keys",
    "end_session_endpoint": "https://login.example.com/tenant/logout",
}
REQUESTS_GET = "user.modules.oidc_provider.requests.get"


def discovery_response(document: dict | None = None) -> mock.Mock:
    response = mock.Mock()
    response.json.return_value = DISCOVERY_DOCUMENT if document is None else document
    return response


def unreachable() -> requests.ConnectionError:
    return requests.ConnectionError("unreachable")
