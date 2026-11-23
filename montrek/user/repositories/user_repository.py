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

    def link_oidc_subject(self, user: MontrekUser, issuer: str, subject: str) -> None:
        user.oidc_issuer, user.oidc_subject = issuer, subject
        user.save(update_fields=["oidc_issuer", "oidc_subject"])


class UserAssignmentRepository(MontrekRepository):
    hub_class = UserAssignmentHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(UserAssignmentSatellite, ["user__email"])
