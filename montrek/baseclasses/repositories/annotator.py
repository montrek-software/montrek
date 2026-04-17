from dataclasses import dataclass
from django.apps.registry import AppRegistryNotReady
from django.db import models
from django.db.models import ExpressionWrapper, Field, Subquery
from django.utils import timezone
from baseclasses.repositories.subquery_builder import (
    LinkedSatelliteSubqueryBuilderBase,
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


@dataclass
class FieldProjection:
    field: str
    outfield: str
    satellite_alias: SatelliteAlias


@dataclass
class LinkedSatelliteAlias:
    alias_name: str
    subquery_builder: LinkedSatelliteSubqueryBuilderBase


@dataclass
class LinkedFieldProjection:
    field: str
    outfield: str
    linked_satellite_alias: LinkedSatelliteAlias


class Annotator:
    def __init__(self, hub_class: type[MontrekHubABC]):
        self.hub_class = hub_class
        self.satellite_aliases: list[SatelliteAlias] = []
        self.field_projections: list[FieldProjection] = []
        self.field_type_map: dict[str, models.Field] = self.get_raw_field_type_map()

        self.raw_annotations: dict[str, SubqueryBuilder] = self.get_raw_annotations()
        self.annotations: dict[str, SubqueryBuilder] = self.raw_annotations.copy()
        self.ts_annotations: dict[str, Subquery] = {}
        self.annotated_satellite_classes: list[type[MontrekSatelliteBaseABC]] = []
        self.annotated_linked_satellite_classes: list[type[MontrekSatelliteBaseABC]] = (
            []
        )
        self.annotated_link_classes: list[type[MontrekLinkABC]] = []
        self.linked_satellite_aliases: list[LinkedSatelliteAlias] = []
        self.linked_field_projections: list[LinkedFieldProjection] = []
        # Tracks all field names (outfields) in registration order so that
        # get_annotated_field_names preserves insertion order across annotations,
        # field_projections, and linked_field_projections.
        self._field_names_in_order: list[str] = list(self.raw_annotations.keys())

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

    def field_projections_to_subqueries(
        self,
    ) -> dict[str, Subquery | ExpressionWrapper]:
        subquery_map = {}
        for field_projection in self.field_projections:
            alias_name = field_projection.satellite_alias.alias_name
            subquery_builder = field_projection.satellite_alias.subquery_builder
            field = field_projection.field
            outfield = field_projection.outfield
            subquery_map[outfield] = subquery_builder.build_subquery(alias_name, field)
        return subquery_map

    def linked_field_projections_to_subqueries(
        self,
    ) -> dict[str, Subquery]:
        subquery_map = {}
        for lfp in self.linked_field_projections:
            alias_name = lfp.linked_satellite_alias.alias_name
            builder = lfp.linked_satellite_alias.subquery_builder
            subquery_map[lfp.outfield] = builder.build_subquery(alias_name, lfp.field)
        return subquery_map

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
        return list(self._field_names_in_order)

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
        for field_projection in self.field_projections:
            if field_projection.outfield == old_field:
                field_projection.outfield = new_field
        for linked_field_projection in self.linked_field_projections:
            if linked_field_projection.outfield == old_field:
                linked_field_projection.outfield = new_field
        if old_field in self.field_type_map:
            self.field_type_map[new_field] = self.field_type_map.pop(old_field)
        for i, name in enumerate(self._field_names_in_order):
            if name == old_field:
                self._field_names_in_order[i] = new_field
                break

    def has_only_static_sats(self) -> bool:
        return not (
            self.get_ts_satellite_classes() or self.get_ts_linked_satellite_classes()
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

        # Use a probe instance to determine whether this link is scalar (one
        # satellite per hub row).  Scalar, non-timeseries links can share a
        # single satellite-pk alias so each additional field costs only a cheap
        # pk-lookup instead of a full link traversal.
        probe_builder = subquery_builder(satellite_class, fields[0], **kwargs)
        is_scalar = (
            not satellite_class.is_timeseries
            and not probe_builder._is_multiple_allowed(probe_builder._hub_field_to)
        )

        if is_scalar:
            linked_alias = self._get_or_create_linked_satellite_alias(
                satellite_class, subquery_builder, probe_builder
            )
            for field in fields:
                outfield = rename_field_map.get(field, field)
                self.linked_field_projections.append(
                    LinkedFieldProjection(
                        field=field,
                        outfield=outfield,
                        linked_satellite_alias=linked_alias,
                    )
                )
                self.set_field_type(field, outfield, satellite_class)
                self._field_names_in_order.append(outfield)
        else:
            for field in fields:
                outfield = rename_field_map.get(field, field)
                self.annotations[outfield] = subquery_builder(
                    satellite_class, field, **kwargs
                )
                self.set_field_type(field, outfield, satellite_class)
                self._field_names_in_order.append(outfield)

                if issubclass(link_class, MontrekManyToManyLinkABC) or (
                    issubclass(link_class, MontrekOneToManyLinkABC)
                    and isinstance(
                        self.annotations[outfield],
                        ReverseLinkedSatelliteSubqueryBuilder,
                    )
                    and agg_func == "string_concat"
                ):
                    self.field_type_map[outfield] = models.CharField(
                        null=True, blank=True
                    )

    def _get_or_create_linked_satellite_alias(
        self,
        satellite_class: type[MontrekSatelliteBaseABC],
        subquery_builder_class: type[SubqueryBuilder],
        probe_builder: LinkedSatelliteSubqueryBuilderBase,
    ) -> LinkedSatelliteAlias:
        """Return an existing alias if the same (satellite, link, config)
        combination has already been registered; otherwise create a new one.

        This ensures that multiple fields from the same scalar linked satellite
        share a single alias subquery rather than each building an independent
        full link traversal.
        """
        for alias in self.linked_satellite_aliases:
            b = alias.subquery_builder
            if (
                type(b) is subquery_builder_class
                and b.satellite_class is satellite_class
                and b.link_class is probe_builder.link_class
                and b.parent_link_classes == probe_builder.parent_link_classes
                and list(b.parent_link_reversed)
                == list(probe_builder.parent_link_reversed)
                and b.link_satellite_filter == probe_builder.link_satellite_filter
                and b.cross_satellite_filters == probe_builder.cross_satellite_filters
            ):
                return alias

        base_name = (
            f"{satellite_class.__name__.lower()}"
            f"__{probe_builder.link_class.__name__.lower()}__lsat"
        )
        existing_names = {a.alias_name for a in self.linked_satellite_aliases}
        alias_name = base_name
        counter = 0
        while alias_name in existing_names:
            counter += 1
            alias_name = f"{base_name}_{counter}"

        new_alias = LinkedSatelliteAlias(
            alias_name=alias_name, subquery_builder=probe_builder
        )
        self.linked_satellite_aliases.append(new_alias)
        return new_alias

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
            self._field_names_in_order.append(outfield)

    def _handle_scalar_satellite(
        self,
        fields: list[str],
        satellite_class: type[MontrekSatelliteBaseABC],
        subquery_builder: type[SubqueryBuilder],
        rename_field_map: dict[str, str],
    ):
        alias_name = f"{satellite_class.__name__.lower()}__sat"
        subquery_builder_inst = subquery_builder(satellite_class=satellite_class)
        satellite_alias = SatelliteAlias(
            alias_name=alias_name,
            subquery_builder=subquery_builder_inst,
        )
        self.satellite_aliases.append(satellite_alias)

        self.add_to_annotated_satellite_classes(satellite_class)

        for field in fields:
            outfield = rename_field_map.get(field, field)
            self.field_projections.append(
                FieldProjection(
                    satellite_alias=satellite_alias, field=field, outfield=outfield
                )
            )
            self.set_field_type(field, outfield, satellite_class)
            self._field_names_in_order.append(outfield)

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
