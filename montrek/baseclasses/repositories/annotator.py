from django.db.models import Subquery
from baseclasses.repositories.subquery_builder import (
    SubqueryBuilder,
)
from baseclasses.models import MontrekSatelliteABC


class Annotator:
    def __init__(self):
        self.annotations: dict[str, SubqueryBuilder] = {}
        self.ts_annotations: dict[str, Subquery] = {}

    def subquery_builder_to_annotations(
        self,
        fields: list[str],
        satellite_class: type[MontrekSatelliteABC],
        subquery_builder: type[SubqueryBuilder],
        **kwargs,
    ):
        for field in fields:
            self.annotations[field] = subquery_builder(satellite_class, field, **kwargs)

    def build(self):
        return {
            field: subquery_builder.build()
            for field, subquery_builder in self.annotations.items()
        }
