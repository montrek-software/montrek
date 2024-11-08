from django.db.models import Field, Subquery
from django.utils import timezone
from baseclasses.repositories.subquery_builder import (
    SubqueryBuilder,
)
from baseclasses.models import MontrekSatelliteABC


class Annotator:
    def __init__(self):
        self.annotations: dict[str, SubqueryBuilder] = {}
        self.ts_annotations: dict[str, Subquery] = {}
        self.annotated_satellite_classes: list[type[MontrekSatelliteABC]] = []

    def subquery_builder_to_annotations(
        self,
        fields: list[str],
        satellite_class: type[MontrekSatelliteABC],
        subquery_builder: type[SubqueryBuilder],
        **kwargs,
    ):
        for field in fields:
            self.annotations[field] = subquery_builder(satellite_class, field, **kwargs)
            self._add_to_annotated_satellite_classes(satellite_class)

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

    def _add_to_annotated_satellite_classes(
        self, satellite_class: type[MontrekSatelliteABC]
    ):
        if satellite_class not in self.annotated_satellite_classes:
            self.annotated_satellite_classes.append(satellite_class)
