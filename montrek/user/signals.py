from django.conf import settings
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

    hub = UserAssignmentHub.objects.create()
    value_date_list, _ = ValueDateList.objects.get_or_create(value_date=None)
    UserAssignmentHubValueDate.objects.create(hub=hub, value_date_list=value_date_list)
    UserAssignmentSatellite.objects.create(hub_entity=hub, user=instance)
