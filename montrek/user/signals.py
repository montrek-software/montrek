from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_assignment(sender, instance, **kwargs):
    from baseclasses.models import ValueDateList
    from user.models import (
        UserAssignmentHub,
        UserAssignmentHubValueDate,
        UserAssignmentSatellite,
    )

    if UserAssignmentSatellite.objects.filter(user=instance).exists():
        return

    value_date_list = ValueDateList.objects.filter(value_date=None).first()
    if value_date_list is None:
        value_date_list = ValueDateList.objects.create(value_date=None)

    try:
        with transaction.atomic():
            hub = UserAssignmentHub.objects.create()
            UserAssignmentHubValueDate.objects.create(
                hub=hub, value_date_list=value_date_list
            )
            UserAssignmentSatellite.objects.create(hub_entity=hub, user=instance)
    except IntegrityError:
        pass
