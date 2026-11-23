import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.db.models import QuerySet
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from user.modules.oidc_provider import OidcProvider
from user.repositories.user_repository import MontrekUserRepository

logger = logging.getLogger(__name__)


class MontrekOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """Signs users in through the OpenID provider.

    A user is the provider's subject (the sub claim of its issuer), not an
    email: the provider may let its users change their email, or hand out one
    another account had (nOAuth). At the first sign-in through the provider,
    montrek links the user it has under that email to the subject; from then on
    only the subject counts. An account already linked to another subject of
    the same issuer is never taken over by an email. A new email at the
    provider becomes the user's, unless another user has it or the user is
    the one ADMIN_EMAIL provisions.
    """

    get_settings = staticmethod(OidcProvider.get_settings)

    def verify_token(self, token: Any, **kwargs: Any) -> dict[str, Any]:
        payload = super().verify_token(token, **kwargs)
        # mozilla-django-oidc checks the signature, not who issued the token.
        # With an issuer URL configured, only that issuer's tokens count.
        issuer = settings.OIDC_ISSUER_URL
        if issuer and payload.get("iss") != issuer:
            raise SuspiciousOperation("ID token from another issuer")
        return payload

    def get_userinfo(
        self, access_token: Any, id_token: Any, payload: dict[str, Any] | None
    ) -> dict[str, Any]:
        claims = super().get_userinfo(access_token, id_token, payload)
        # OpenID Connect Core 5.3.2: the userinfo must be the ID token's
        # subject's. payload is None for REST API tokens, which have no ID token.
        if payload is not None and claims.get("sub") != payload.get("sub"):
            raise SuspiciousOperation("Userinfo of another subject than the ID token")
        return claims

    def verify_claims(self, claims: dict[str, Any]) -> bool:
        return bool(claims.get("sub")) and super().verify_claims(claims)

    def filter_users_by_claims(self, claims: dict[str, Any]) -> QuerySet:
        issuer = OidcProvider.issuer()
        users = MontrekUserRepository()
        linked = users.with_oidc_subject(issuer, claims["sub"])
        if linked.exists():
            return linked
        by_email = users.with_email(claims.get("email") or "")
        # Emails are unique only as stored, so Person@ and person@ can be two
        # users: which one the provider means is unknown.
        if by_email.count() > 1:
            raise SuspiciousOperation("Several users have the provider's email")
        unlinked = by_email.exclude(oidc_issuer=issuer)
        if by_email.exists() and not unlinked.exists():
            logger.warning(
                "OIDC sign-in refused: %s belongs to another subject of %s. If the "
                "user's account at the provider was recreated, clear the user's "
                "provider link in the admin.",
                claims.get("email"),
                issuer,
            )
        return unlinked

    def create_user(self, claims: dict[str, Any]) -> Any:
        if MontrekUserRepository().with_email(claims.get("email") or "").exists():
            # Only reached when the email belongs to a user linked to another
            # subject (filter_users_by_claims).
            raise SuspiciousOperation("Email of a user linked to another subject")
        # The base class passes a username derived from the email as the first
        # argument, which MontrekUserManager.create_user takes as the password:
        # anyone knowing the email could sign in with it wherever the Django
        # password is accepted. A user from the provider gets none.
        return self.UserModel.objects.create_user(
            email=claims.get("email"),
            oidc_issuer=OidcProvider.issuer(),
            oidc_subject=claims["sub"],
        )

    def update_user(self, user: Any, claims: dict[str, Any]) -> Any:
        users = MontrekUserRepository()
        link = (OidcProvider.issuer(), claims["sub"])
        if (user.oidc_issuer, user.oidc_subject) != link and not (
            users.link_oidc_subject(user, *link)
        ):
            raise SuspiciousOperation("User linked to another subject meanwhile")
        email = claims.get("email")
        if not email or email.lower() == user.email.lower():
            return user
        if self.is_provisioned_admin(user):
            # The release step creates a superuser under ADMIN_EMAIL whenever
            # none has it, and that one would be linked to whoever next signs
            # in with it.
            logger.warning(
                "OIDC sign-in of %s: the email stays ADMIN_EMAIL, not the "
                "provider's %s.",
                user.email,
                email,
            )
        elif not users.change_email(user, email):
            logger.warning(
                "OIDC sign-in of %s: the provider's email %s belongs to another "
                "user, so it is kept.",
                user.email,
                email,
            )
        return user

    @staticmethod
    def is_provisioned_admin(user: Any) -> bool:
        admin_email = settings.ADMIN_EMAIL or ""
        return user.email.lower() == admin_email.lower()
