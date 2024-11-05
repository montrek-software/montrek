from django.db.models import Subquery
from baseclasses.repositories.subquery_builder import (
    SubqueryBuilder,
)


class Annotator:
    def __init__(self):
        self.annotations: dict[str, Subquery] = {}
        self.ts_annotations: dict[str, Subquery] = {}

    def query_to_annotations(
        self, fields: list[str], subquery_builder: SubqueryBuilder
    ):
        for field in fields:
            self.annotations[field] = subquery_builder.get_subquery(field)
