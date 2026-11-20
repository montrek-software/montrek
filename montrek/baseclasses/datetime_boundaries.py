import datetime

from django.utils import timezone


class DatetimeBoundaries:
    """The open ends of a validity period: the first and last representable instant.

    They are pinned to UTC, as shifting them by a local offset (e.g. Europe/Berlin)
    moves them outside the representable datetime range. Converting such a value to
    another time zone therefore only swaps its time zone.
    """

    MIN = datetime.datetime.min.replace(tzinfo=datetime.UTC)
    MAX = datetime.datetime.max.replace(tzinfo=datetime.UTC)

    @classmethod
    def is_boundary(cls, value: datetime.datetime) -> bool:
        return value.date() in (cls.MIN.date(), cls.MAX.date())

    @classmethod
    def to_naive_local_time(cls, value: datetime.datetime) -> datetime.datetime:
        if timezone.is_naive(value):
            return value
        if cls.is_boundary(value):
            return value.replace(tzinfo=None)
        return timezone.make_naive(value)
