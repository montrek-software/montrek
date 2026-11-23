from django.contrib.auth.models import Group
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

    def assign_roles(
        self, user: MontrekUser, group_names: set[str], is_staff: bool | None
    ) -> set[str]:
        """Puts `user` in exactly the groups named, of those that exist, and
        sets is_staff unless it is None. Returns the names without a group."""
        groups = list(Group.objects.filter(name__in=group_names))
        with transaction.atomic():
            # Locked and read again: `user` may be older than a concurrent
            # sign-in's change, and two sign-ins apply their roles one after
            # the other.
            persisted = MontrekUser.objects.select_for_update().get(pk=user.pk)
            persisted.groups.set(groups)
            if is_staff is not None and persisted.is_staff != is_staff:
                persisted.is_staff = is_staff
                persisted.save(update_fields=["is_staff"])
            user.is_staff = persisted.is_staff
        return group_names - {group.name for group in groups}


class UserAssignmentRepository(MontrekRepository):
    hub_class = UserAssignmentHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(UserAssignmentSatellite, ["user__email"])
