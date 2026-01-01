from dataclasses import dataclass
from typing import Any
from django.apps.registry import AppRegistryNotReady
from django.db.models import Field, OuterRef, Subquery
from django.utils import timezone
from baseclasses.repositories.subquery_builder import (
    SubqueryBuilder,
    ValueDateSubqueryBuilder,
    HubEntityIdSubqueryBuilder,
    CreatedAtSubqueryBuilder,
    CreatedBySubqueryBuilder,
    CommentSubqueryBuilder,
)
from baseclasses.models import (
    MontrekLinkABC,
    MontrekSatelliteABC,
    MontrekHubABC,
    MontrekSatelliteBaseABC,
)


@dataclass
class SatelliteAlias:
    alias_name: str
    subquery_builder: SubqueryBuilder


class Annotator:
    def __init__(self, hub_class: type[MontrekHubABC]):
        self.hub_class = hub_class
        self.satellite_aliases: list[SatelliteAlias] = []
        self.field_projections: dict[str, Subquery] = {}

        self.raw_annotations: dict[str, SubqueryBuilder] = self.get_raw_annotations()
        self.annotations: dict[str, SubqueryBuilder] = self.raw_annotations.copy()
        self.ts_annotations: dict[str, Subquery] = {}
        self.annotated_satellite_classes: list[type[MontrekSatelliteABC]] = []
        self.annotated_linked_satellite_classes: list[type[MontrekSatelliteABC]] = []
        self.annotated_link_classes: list[type[MontrekLinkABC]] = []

    def get_raw_annotations(self) -> dict[str, SubqueryBuilder]:
        return {
            "value_date": ValueDateSubqueryBuilder(),
            "hub_entity_id": HubEntityIdSubqueryBuilder(self.hub_class),
            "created_at": CreatedAtSubqueryBuilder(self.hub_class),
            "created_by": CreatedBySubqueryBuilder(self.hub_class),
            "comment": CommentSubqueryBuilder(self.hub_class),
        }

    def subquery_builder_to_annotations(
        self,
        fields: list[str],
        satellite_class: type[MontrekSatelliteBaseABC],
        subquery_builder: type[SubqueryBuilder],
        *,
        rename_field_map: dict[str, str] | None = None,
        **kwargs,
    ):
        rename_field_map = {} if rename_field_map is None else rename_field_map
        if "link_class" in kwargs:
            # TODO: Implement link with aliases
            self.annotated_link_classes.append(kwargs["link_class"])
            for field in fields:
                outfield = rename_field_map.get(field, field)
                self.annotations[outfield] = subquery_builder(
                    satellite_class, field, **kwargs
                )
            return
        alias_name = satellite_class.__name__.lower()

        self.satellite_aliases.append(
            SatelliteAlias(
                alias_name=alias_name,
                subquery_builder=subquery_builder(satellite_class=satellite_class),
            )
        )

        for field in fields:
            outfield = rename_field_map.get(field, field)
            self.field_projections[outfield] = Subquery(
                satellite_class.objects.filter(pk=OuterRef(alias_name)).values(field)
            )

    def build(self, reference_date: timezone.datetime) -> dict[str, Subquery]:
        return {
            field: subquery_builder.build(reference_date)
            for field, subquery_builder in self.annotations.items()
        }

    def satellite_fields(self) -> list[Field]:
        fields = []
        for satellite_class in self.annotated_satellite_classes:
            fields.extend(satellite_class.get_value_fields())
        return fields

    def satellite_fields_names(self) -> list[object | str]:
        return [field.name for field in self.satellite_fields()]

    def get_annotated_field_names(self) -> list[str]:
        return list(self.annotations.keys())

    def get_satellite_classes(self) -> list[type[MontrekSatelliteABC]]:
        return self.annotated_satellite_classes

    def get_ts_satellite_classes(self) -> list[type[MontrekSatelliteABC]]:
        return self._get_ts_satellite_classes(self.annotated_satellite_classes)

    def get_linked_satellite_classes(self) -> list[type[MontrekSatelliteABC]]:
        return self.annotated_linked_satellite_classes

    def get_ts_linked_satellite_classes(self) -> list[type[MontrekSatelliteABC]]:
        return self._get_ts_satellite_classes(self.annotated_linked_satellite_classes)

    def get_link_classes(self) -> list[type[MontrekLinkABC]]:
        return self.annotated_link_classes

    def add_to_annotated_satellite_classes(
        self, satellite_class: type[MontrekSatelliteABC]
    ):
        try:
            related_hub_class = satellite_class.get_related_hub_class()
            if related_hub_class == self.hub_class:
                self._add_class(self.annotated_satellite_classes, satellite_class)
            else:
                self._add_class(
                    self.annotated_linked_satellite_classes, satellite_class
                )
        except AppRegistryNotReady:
            return

    def get_annotated_field_map(self) -> dict[str, Any]:
        return {
            field: subquery_builder.field_type
            for field, subquery_builder in self.annotations.items()
        }

    def rename_field(self, old_field: str, new_field: str):
        self.annotations[new_field] = self.annotations.pop(old_field)

    def has_only_static_sats(self) -> bool:
        return not (
            self.get_ts_satellite_classes() or self.get_ts_linked_satellite_classes()
        )

    def _add_class(
        self,
        class_list: list[type[MontrekSatelliteABC]],
        sat_class: type[MontrekSatelliteABC],
    ):
        if sat_class not in class_list:
            class_list.append(sat_class)

    def _get_ts_satellite_classes(
        self, satellite_classes: list[type[MontrekSatelliteABC]]
    ) -> list[type[MontrekSatelliteABC]]:
        return [
            satellite_class
            for satellite_class in satellite_classes
            if satellite_class.is_timeseries
        ]
