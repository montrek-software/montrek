from dataclasses import dataclass
from django.apps.registry import AppRegistryNotReady
from django.db import models
from django.db.models import Field, OuterRef, Subquery
from django.utils import timezone
from baseclasses.repositories.subquery_builder import (
    ReverseLinkedSatelliteSubqueryBuilder,
    SubqueryBuilder,
    TSSumFieldSubqueryBuilder,
    ValueDateSubqueryBuilder,
    HubEntityIdSubqueryBuilder,
    CreatedAtSubqueryBuilder,
    CreatedBySubqueryBuilder,
    CommentSubqueryBuilder,
)
from baseclasses.models import (
    MontrekLinkABC,
    MontrekHubABC,
    MontrekManyToManyLinkABC,
    MontrekOneToManyLinkABC,
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
        self.field_type_map: dict[str, models.Field] = self.get_raw_field_type_map()

        self.raw_annotations: dict[str, SubqueryBuilder] = self.get_raw_annotations()
        self.annotations: dict[str, SubqueryBuilder] = self.raw_annotations.copy()
        self.ts_annotations: dict[str, Subquery] = {}
        self.annotated_satellite_classes: list[type[MontrekSatelliteBaseABC]] = []
        self.annotated_linked_satellite_classes: list[type[MontrekSatelliteBaseABC]] = (
            []
        )
        self.annotated_link_classes: list[type[MontrekLinkABC]] = []

    def get_raw_annotations(self) -> dict[str, SubqueryBuilder]:
        return {
            "value_date": ValueDateSubqueryBuilder(),
            "hub_entity_id": HubEntityIdSubqueryBuilder(self.hub_class),
            "created_at": CreatedAtSubqueryBuilder(self.hub_class),
            "created_by": CreatedBySubqueryBuilder(self.hub_class),
            "comment": CommentSubqueryBuilder(self.hub_class),
        }

    def get_raw_field_type_map(self) -> dict[str, models.Field]:
        return {
            "value_date": models.DateField(),
            "hub_entity_id": models.IntegerField(),
            "created_at": models.DateTimeField(),
            "created_by": models.EmailField(),
            "comment": models.CharField(),
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
        rename_field_map = rename_field_map or {}

        if "link_class" in kwargs:
            self._handle_linked_satellite(
                fields, satellite_class, subquery_builder, rename_field_map, **kwargs
            )
            return

        ts_agg_func = kwargs.get("ts_agg_func")
        if satellite_class.is_timeseries and ts_agg_func == "sum":
            self._handle_ts_sum_satellite(fields, satellite_class, rename_field_map)
            return

        self._handle_scalar_satellite(
            fields, satellite_class, subquery_builder, rename_field_map
        )

    def _handle_linked_satellite(
        self,
        fields: list[str],
        satellite_class: type[MontrekSatelliteBaseABC],
        subquery_builder: type[SubqueryBuilder],
        rename_field_map: dict[str, str],
        **kwargs,
    ):
        link_class = kwargs["link_class"]
        agg_func = kwargs["agg_func"]

        self.annotated_link_classes.append(link_class)
        self.add_to_annotated_satellite_classes(satellite_class)

        for field in fields:
            outfield = rename_field_map.get(field, field)

            self.annotations[outfield] = subquery_builder(
                satellite_class, field, **kwargs
            )
            self.set_field_type(field, outfield, satellite_class)

            if issubclass(link_class, MontrekManyToManyLinkABC) or (
                issubclass(link_class, MontrekOneToManyLinkABC)
                and isinstance(
                    self.annotations[outfield],
                    ReverseLinkedSatelliteSubqueryBuilder,
                )
                and agg_func == "string_concat"
            ):
                self.field_type_map[outfield] = models.CharField(null=True, blank=True)

    def _handle_ts_sum_satellite(
        self,
        fields: list[str],
        satellite_class: type[MontrekSatelliteBaseABC],
        rename_field_map: dict[str, str],
    ):
        self.add_to_annotated_satellite_classes(satellite_class)

        for field in fields:
            outfield = rename_field_map.get(field, field)

            self.annotations[outfield] = TSSumFieldSubqueryBuilder(
                satellite_class, field
            )
            self.set_field_type(field, outfield, satellite_class)

    def _handle_scalar_satellite(
        self,
        fields: list[str],
        satellite_class: type[MontrekSatelliteBaseABC],
        subquery_builder: type[SubqueryBuilder],
        rename_field_map: dict[str, str],
    ):
        alias_name = f"{satellite_class.__name__.lower()}__sat"

        self.satellite_aliases.append(
            SatelliteAlias(
                alias_name=alias_name,
                subquery_builder=subquery_builder(satellite_class=satellite_class),
            )
        )

        self.add_to_annotated_satellite_classes(satellite_class)

        for field in fields:
            outfield = rename_field_map.get(field, field)

            sat_query = satellite_class.objects.filter(pk=OuterRef(alias_name))
            self.field_projections[outfield] = Subquery(sat_query.values(field))

            self.set_field_type(field, outfield, satellite_class)

    def build(self, reference_date: timezone.datetime) -> dict[str, Subquery]:
        return {
            field: subquery_builder.build(reference_date)
            for field, subquery_builder in self.annotations.items()
        }

    def set_field_type(
        self, field: str, outfield: str, satellite_class: type[MontrekSatelliteBaseABC]
    ) -> None:
        field_parts = field.split("__")
        field_type = satellite_class._meta.get_field(field_parts[0])
        if isinstance(field_type, models.ForeignKey):
            field_type = models.IntegerField(null=True, blank=True)
        self.field_type_map[outfield] = field_type.clone()

    def satellite_fields(self) -> list[Field]:
        fields = []
        for satellite_class in self.annotated_satellite_classes:
            fields.extend(satellite_class.get_value_fields())
        return fields

    def satellite_fields_names(self) -> list[object | str]:
        return [field.name for field in self.satellite_fields()]

    def get_annotated_field_names(self) -> list[str]:
        return list(self.annotations.keys()) + list(self.field_projections.keys())

    def get_satellite_classes(self) -> list[type[MontrekSatelliteBaseABC]]:
        return self.annotated_satellite_classes

    def get_ts_satellite_classes(self) -> list[type[MontrekSatelliteBaseABC]]:
        return self._get_ts_satellite_classes(self.annotated_satellite_classes)

    def get_linked_satellite_classes(self) -> list[type[MontrekSatelliteBaseABC]]:
        return self.annotated_linked_satellite_classes

    def get_ts_linked_satellite_classes(self) -> list[type[MontrekSatelliteBaseABC]]:
        return self._get_ts_satellite_classes(self.annotated_linked_satellite_classes)

    def get_link_classes(self) -> list[type[MontrekLinkABC]]:
        return self.annotated_link_classes

    def add_to_annotated_satellite_classes(
        self, satellite_class: type[MontrekSatelliteBaseABC]
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

    def get_annotated_field_map(self) -> dict[str, models.Field]:
        return self.field_type_map

    def rename_field(self, old_field: str, new_field: str):
        if old_field in self.annotations:
            self.annotations[new_field] = self.annotations.pop(old_field)
        if old_field in self.field_projections:
            self.field_projections[new_field] = self.field_projections.pop(old_field)

    def has_only_static_sats(self) -> bool:
        return not (
            self.get_ts_satellite_classes() or self.get_ts_linked_satellite_classes()
        )

    def _add_class(
        self,
        class_list: list[type[MontrekSatelliteBaseABC]],
        sat_class: type[MontrekSatelliteBaseABC],
    ):
        if sat_class not in class_list:
            class_list.append(sat_class)

    def _get_ts_satellite_classes(
        self, satellite_classes: list[type[MontrekSatelliteBaseABC]]
    ) -> list[type[MontrekSatelliteBaseABC]]:
        return [
            satellite_class
            for satellite_class in satellite_classes
            if satellite_class.is_timeseries
        ]
