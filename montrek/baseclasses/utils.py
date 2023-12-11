import datetime
from datetime import timedelta
from typing import Tuple
from django.utils import timezone

#TODO Make universal MontrekDateTime class

def montrek_time(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0
) -> timezone.datetime:
    return timezone.make_aware(
        datetime.datetime(year, month, day, hour, minute),
        timezone=timezone.get_current_timezone(),
    )

def montrek_today() -> timezone.datetime:
    return timezone.now().date()

def montrek_date_string(date: timezone.datetime) -> str:
    return date.strftime("%Y-%m-%d")

def get_date_range_dates(request) -> Tuple[str, str]:
    default_start_date = montrek_date_string(montrek_today() - timedelta(days=30))
    default_end_date = montrek_date_string(montrek_today())

    start_date_str = request.session.get("start_date", default_start_date)
    end_date_str = request.session.get("end_date", default_end_date)

    return start_date_str, end_date_str
