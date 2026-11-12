from collections.abc import Iterable
from dataclasses import dataclass

from django.apps import apps
from django.db import connection
from django.db.models import (
    Count,
    F,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
)
from django.db.models.functions import Coalesce

from baseclasses.models import HubValueDate, ValueDateList


@dataclass(frozen=True)
class HubValueDateCopyFinding:
    model: type[HubValueDate]
    has_column: bool
    # Rows whose copy differs from their value date row
    stale_copies: int = 0
    # Hubs with more than one row on the same date, or more than one undated row
    hubs_with_duplicate_dates: int = 0

    @property
    def is_consistent(self) -> bool:
        return (
            self.has_column
            and not self.stale_copies
            and not self.hubs_with_duplicate_dates
        )


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
    def latest_row_ids(
        hub_value_date_model: type[HubValueDate], hubs: QuerySet
    ) -> QuerySet:
        """Id of the latest row of each of the hubs: the newest dated row, or
        the undated row if the hub has no dated one. One lookup per hub in the
        index on ``(hub, value_date_copy)``."""
        rows_of_hub = hub_value_date_model.objects.filter(hub_id=OuterRef("pk"))
        latest_dated = (
            rows_of_hub.filter(value_date_copy__isnull=False)
            .order_by("-value_date_copy")
            .values("id")[:1]
        )
        undated = (
            rows_of_hub.filter(value_date_copy__isnull=True)
            .order_by("id")
            .values("id")[:1]
        )
        return hubs.annotate(
            latest_id=Coalesce(Subquery(latest_dated), Subquery(undated))
        ).values("latest_id")

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
        # Without stale copies and duplicate dates, ordering by the copy picks
        # the same latest row per hub as ordering by the value date row.
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
        hubs_with_duplicate_dates = (
            model.objects.values("hub_id", "value_date_copy")
            .annotate(rows=Count("id"))
            .filter(rows__gt=1)
            .values("hub_id")
            .distinct()
            .count()
        )
        return HubValueDateCopyFinding(
            model=model,
            has_column=True,
            stale_copies=stale_copies,
            hubs_with_duplicate_dates=hubs_with_duplicate_dates,
        )
