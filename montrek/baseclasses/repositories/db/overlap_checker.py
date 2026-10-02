"""Find versions that are valid at the same time for the same hub.

Repositories join the satellite version valid at the reference date, and the
link valid at the reference date for scalar links. Two such rows valid at the
same time make the join return the outer row once per match, silently
duplicating it, so this has to hold for the data:

* a satellite has at most one version per hub (static) or per hub value date
  (timeseries) at any time,
* a one-to-one link has at most one valid link per ``hub_in`` and per
  ``hub_out``, and a one-to-many link one per ``hub_in`` - the sides read as a
  single value. Many-to-many links are always aggregated.
"""

from dataclasses import dataclass, field

from django.apps import apps
from django.db import connection, models
from django.db.models import Exists, OuterRef

from baseclasses.models import (
    MontrekOneToManyLinkABC,
    MontrekOneToOneLinkABC,
    MontrekSatelliteABC,
    MontrekTimeSeriesSatelliteABC,
)

MAX_REPORTED_KEYS = 10


@dataclass
class OverlapFinding:
    model: type[models.Model]
    key_field: str
    # The first MAX_REPORTED_KEYS affected keys, ascending.
    key_values: list[int] = field(default_factory=list)


def find_overlapping_versions(
    app_labels: tuple[str, ...] = (),
) -> list[OverlapFinding]:
    """Check every satellite and link model, or those of ``app_labels``.

    Models without a table in the database (e.g. test-only models) are
    skipped.
    """
    existing_tables = set(connection.introspection.table_names())
    findings = []
    for model, key_field in _models_to_check(app_labels):
        if model._meta.db_table not in existing_tables:
            continue
        key_values = _overlapping_keys(model, key_field)
        if key_values:
            findings.append(OverlapFinding(model, key_field, key_values))
    return findings


def _models_to_check(
    app_labels: tuple[str, ...],
) -> list[tuple[type[models.Model], str]]:
    to_check: list[tuple[type[models.Model], str]] = []
    for model in apps.get_models():
        if app_labels and model._meta.app_label not in app_labels:
            continue
        if issubclass(model, MontrekSatelliteABC):
            to_check.append((model, "hub_entity"))
        elif issubclass(model, MontrekTimeSeriesSatelliteABC):
            to_check.append((model, "hub_value_date"))
        elif issubclass(model, MontrekOneToOneLinkABC):
            to_check.extend([(model, "hub_in"), (model, "hub_out")])
        elif issubclass(model, MontrekOneToManyLinkABC):
            to_check.append((model, "hub_in"))
    return to_check


def _overlapping_keys(model: type[models.Model], key_field: str) -> list[int]:
    # Validity is half-open [state_date_start, state_date_end): two rows
    # overlap if each one starts before the other ends.
    other_valid_row = (
        model._default_manager.filter(
            **{key_field: OuterRef(key_field)},
            state_date_start__lt=OuterRef("state_date_end"),
            state_date_end__gt=OuterRef("state_date_start"),
        )
        .exclude(pk=OuterRef("pk"))
        .values("pk")
    )
    key_column = f"{key_field}_id"
    return list(
        model._default_manager.filter(Exists(other_valid_row))
        .order_by(key_column)
        .values_list(key_column, flat=True)
        .distinct()[:MAX_REPORTED_KEYS]
    )
