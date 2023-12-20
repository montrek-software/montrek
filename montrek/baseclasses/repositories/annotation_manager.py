
from typing import Type, List
from baseclasses.repositories.subquery_builder import (
    SubqueryBuilder,
)
class AnnotationsManager:
    def __init__(self, subquery_builder: SubqueryBuilder):
        self.annotations = {}
        self.subquery_builder = subquery_builder

    def query_to_annotations(self, fields: List[str], **kwargs) -> dict:
        raise NotImplementedError( "AnnotationsManager has no query_to_annotations method!"
        )


class SatelliteAnnotationsManager(AnnotationsManager):
    def query_to_annotations(self, fields: List[str], **kwargs) -> dict:
        for field in fields:
            subquery = self.subquery_builder.get_subquery(field)
            self.annotations[field] = subquery


class LinkAnnotationsManager(AnnotationsManager):
    def __init__(self, subquery_builder: SubqueryBuilder, satellite_class_name: str):
        self.satellite_class_name = satellite_class_name
        super().__init__(subquery_builder)

    def query_to_annotations(self, fields: List[str], **kwargs) -> dict:
        for field in fields:
            subquery = self.subquery_builder.get_subquery(field)
            field = f"{field}"
            self.annotations[field] = subquery

