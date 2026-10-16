"""Satellite hashes for data migrations.

Models from ``apps.get_model`` have the fields of the migration state but none
of the satellite methods, so these helpers compute the hashes like
``MontrekSatelliteBaseABC`` does, from field lists frozen in the migration in
the order of the model at that time. Adding a field to a satellite changes
the ``hash_value`` of every existing row; without recomputing it the next
unchanged upload would create a new version of each one.
"""

import datetime
from typing import Any

from baseclasses.models import MontrekSatelliteABC
from baseclasses.utils import datetime_to_montrek_time


def to_hash(value: str) -> str:
    return MontrekSatelliteABC.convert_string_to_hash(value)


def fields_string(satellite: Any, fields: tuple[str, ...]) -> str:
    values = []
    for field in fields:
        value = getattr(satellite, field)
        if isinstance(value, datetime.datetime):
            value = datetime_to_montrek_time(value)
        values.append(str(value))
    return "".join(values)


def identifier_hash(satellite: Any, identifier_fields: tuple[str, ...]) -> str:
    return to_hash(fields_string(satellite, identifier_fields))


def value_hash(satellite: Any, value_fields: tuple[str, ...]) -> str:
    return to_hash(fields_string(satellite, value_fields))


def recompute_hash_values(satellite_model: Any, value_fields: tuple[str, ...]) -> None:
    satellites = list(satellite_model.objects.all())
    for satellite in satellites:
        satellite.hash_value = value_hash(satellite, value_fields)
    satellite_model.objects.bulk_update(satellites, ["hash_value"], batch_size=1000)
