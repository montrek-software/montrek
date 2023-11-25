import datetime
from django.utils import timezone


def montrek_time(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0
) -> timezone.datetime:
    return timezone.make_aware(
        datetime.datetime(year, month, day, hour, minute),
        timezone=timezone.get_current_timezone(),
    )
