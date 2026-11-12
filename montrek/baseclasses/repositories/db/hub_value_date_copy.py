from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast

from django.apps import apps
from django.db import connection, models
from django.db.models import (
    Exists,
    F,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
)

from baseclasses.models import HubValueDate, ValueDateList


@dataclass(frozen=True)
class HubValueDateCopyFinding:
    model: type[HubValueDate]
    has_column: bool
    # Rows whose copy differs from their value date row
    stale_copies: int = 0

    @property
    def is_consistent(self) -> bool:
        return self.has_column and not self.stale_copies


class HubValueDateCopy:
    """``HubValueDate.value_date_copy`` of all hub value date models."""

    def __init__(self, app_labels: Iterable[str] = ()):
        app_labels = set(app_labels)
        # Unmanaged models have no table that migrations would add the copy to
        self.models: list[type[HubValueDate]] = [
            model
            for model in apps.get_models()
            if issubclass(model, HubValueDate)
            and model._meta.managed
            and (not app_labels or model._meta.app_label in app_labels)
        ]

    @staticmethod
    def latest_rows(hub_value_date_model: type[HubValueDate], hubs: QuerySet) -> Q:
        """The latest rows of each of the hubs: its rows on its newest date, or
        its undated rows if it has no dated one. Two id sets, as one condition
        covering both cases keeps Postgres from looking the rows up per hub in
        the index on ``(hub, value_date_copy)``."""
        hub_field = cast(models.ForeignKey, hub_value_date_model._meta.get_field("hub"))
        rows = hub_field.related_query_name()
        dated_rows_of_hub = hub_value_date_model.objects.filter(
            hub_id=OuterRef("pk"), value_date_copy__isnull=False
        )
        latest_date = dated_rows_of_hub.order_by("-value_date_copy").values(
            "value_date_copy"
        )[:1]
        on_latest_date = hubs.filter(
            **{f"{rows}__value_date_copy": Subquery(latest_date)}
        ).values(f"{rows}__id")
        undated = (
            hubs.filter(~Exists(dated_rows_of_hub))
            .filter(
                **{f"{rows}__isnull": False, f"{rows}__value_date_copy__isnull": True}
            )
            .values(f"{rows}__id")
        )
        return Q(id__in=on_latest_date) | Q(id__in=undated)

    @staticmethod
    def has_column(model: type[HubValueDate]) -> bool:
        """False as long as the migration adding the copy has not run, or the
        table does not exist (yet), as for models created by tests."""
        table = model._meta.db_table
        with connection.cursor() as cursor:
            if table not in connection.introspection.table_names(cursor):
                return False
            columns = connection.introspection.get_table_description(cursor, table)
        return any(column.name == "value_date_copy" for column in columns)

    def fill(self) -> dict[type[HubValueDate], int]:
        """Copy the date into the dated rows without a copy, as rows written
        before the copy existed have none. Returns the rows filled per model;
        models whose table has no column yet are left out."""
        value_date = ValueDateList.objects.filter(
            pk=OuterRef("value_date_list_id")
        ).values("value_date")[:1]
        filled = {}
        for model in self.models:
            if not self.has_column(model):
                continue
            filled[model] = model.objects.filter(
                value_date_copy__isnull=True,
                value_date_list__value_date__isnull=False,
            ).update(value_date_copy=Subquery(value_date))
        return filled

    def check(self) -> list[HubValueDateCopyFinding]:
        return [self._check_model(model) for model in self.models]

    def _check_model(self, model: type[HubValueDate]) -> HubValueDateCopyFinding:
        # Without stale copies, the latest rows by copy are those by value
        # date row.
        if not self.has_column(model):
            return HubValueDateCopyFinding(model=model, has_column=False)
        date = "value_date_list__value_date"
        stale_copies = model.objects.filter(
            Q(value_date_copy__isnull=True, **{f"{date}__isnull": False})
            | Q(value_date_copy__isnull=False, **{f"{date}__isnull": True})
            | (
                Q(value_date_copy__isnull=False, **{f"{date}__isnull": False})
                & ~Q(value_date_copy=F(date))
            )
        ).count()
        return HubValueDateCopyFinding(
            model=model,
            has_column=True,
            stale_copies=stale_copies,
        )
