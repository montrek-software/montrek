# utils/keycloak_config.py

from django.conf import settings


def get_keycloak_base_url():
    return f"http://{settings.DEPLOY_HOST}:{settings.KEYCLOAK_PORT}/realms/{settings.KEYCLOAK_REALM}"


def get_oidc_endpoints():
    base = get_keycloak_base_url()
    return {
        "authorization": base + "/protocol/openid-connect/auth",
        "token": base + "/protocol/openid-connect/token",
        "userinfo": base + "/protocol/openid-connect/userinfo",
        "jwks": base + "/protocol/openid-connect/certs",
        "logout": base + "/protocol/openid-connect/logout",
    }
