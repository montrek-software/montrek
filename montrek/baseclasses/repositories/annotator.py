from django.db.models import Field, Subquery
from django.utils import timezone
from baseclasses.repositories.subquery_builder import (
    SubqueryBuilder,
    ValueDateSubqueryBuilder,
    HubEntityIdSubqueryBuilder,
    CreatedAtSubqueryBuilder,
    CreatedBySubqueryBuilder,
    CommentSubqueryBuilder,
)
from baseclasses.models import MontrekLinkABC, MontrekSatelliteABC, MontrekHubABC


class Annotator:
    def __init__(self, hub_class: type[MontrekHubABC]):
        self.hub_class = hub_class
        self.annotations: dict[str, SubqueryBuilder] = self.get_raw_annotations()
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
        satellite_class: type[MontrekSatelliteABC],
        subquery_builder: type[SubqueryBuilder],
        **kwargs,
    ):
        if "link_class" in kwargs:
            self.annotated_link_classes.append(kwargs["link_class"])

        for field in fields:
            self.annotations[field] = subquery_builder(satellite_class, field, **kwargs)
            self.add_to_annotated_satellite_classes(satellite_class)

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

    def get_linked_satellite_classes(self) -> list[type[MontrekSatelliteABC]]:
        return self.annotated_linked_satellite_classes

    def get_link_classes(self) -> list[type[MontrekLinkABC]]:
        return self.annotated_link_classes

    def add_to_annotated_satellite_classes(
        self, satellite_class: type[MontrekSatelliteABC]
    ):
        related_hub_class = satellite_class.get_related_hub_class()
        if related_hub_class == self.hub_class:
            self._add_class(self.annotated_satellite_classes, satellite_class)
        else:
            self._add_class(self.annotated_linked_satellite_classes, satellite_class)

    def _add_class(
        self,
        class_list: list[type[MontrekSatelliteABC]],
        sat_class: type[MontrekSatelliteABC],
    ):
        if sat_class not in class_list:
            class_list.append(sat_class)
