import dataclasses

from django.db.models import QuerySet
from baseclasses.dataclasses.table_elements import StringTableElement


@dataclasses.dataclass
class HistoryDataTable:
    title: str
    queryset: QuerySet

    def __post_init__(self):
        columns = self.queryset.model._meta.fields
        self.elements = [
            StringTableElement(attr=column.name, name=column.name) for column in columns
        ]
