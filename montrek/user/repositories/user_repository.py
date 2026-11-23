from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from baseclasses.repositories.montrek_repository import MontrekRepository
from user.models import MontrekUser, UserAssignmentHub, UserAssignmentSatellite


class MontrekUserRepository:
    def receive(self):
        return MontrekUser.objects.all()

    def with_oidc_subject(self, issuer: str, subject: str) -> QuerySet[MontrekUser]:
        return MontrekUser.objects.filter(oidc_issuer=issuer, oidc_subject=subject)

    def with_email(self, email: str) -> QuerySet[MontrekUser]:
        return MontrekUser.objects.filter(email__iexact=email)

    def change_email(self, user: MontrekUser, email: str) -> bool:
        """Gives `user` the email, unless another user has it; False then."""
        email = MontrekUser.objects.normalize_email(email)
        if self.with_email(email).exclude(pk=user.pk).exists():
            return False
        previous, user.email = user.email, email
        try:
            # A savepoint: a concurrent change to the same email fails here,
            # not the transaction around the sign-in.
            with transaction.atomic():
                user.save(update_fields=["email"])
        except IntegrityError:
            user.email = previous
            return False
        return True

    def link_oidc_subject(self, user: MontrekUser, issuer: str, subject: str) -> bool:
        """Links `user` to the subject, unless another subject of the issuer
        has been linked to it in the meantime; False then."""
        with transaction.atomic():
            persisted = MontrekUser.objects.select_for_update().get(pk=user.pk)
            if persisted.oidc_issuer == issuer and persisted.oidc_subject not in (
                "",
                subject,
            ):
                return False
            user.oidc_issuer, user.oidc_subject = issuer, subject
            user.save(update_fields=["oidc_issuer", "oidc_subject"])
        return True


class UserAssignmentRepository(MontrekRepository):
    hub_class = UserAssignmentHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(UserAssignmentSatellite, ["user__email"])
