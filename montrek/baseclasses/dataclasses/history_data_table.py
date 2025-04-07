import dataclasses

from django.db.models import QuerySet
from reporting.dataclasses.table_elements import StringTableElement

EXCLUDE_COLUMNS = [
    "id",
    "created_at",
    "updated_at",
    "hash_identifier",
    "hash_value",
    "hub_entity",
]


@dataclasses.dataclass
class HistoryDataTable:
    title: str
    queryset: QuerySet

    def __post_init__(self):
        columns = self.queryset.model._meta.fields
        self.elements = []
        self.columns = []
        for column in columns:
            if column.name in EXCLUDE_COLUMNS:
                continue
            self.elements.append(StringTableElement(attr=column.name, name=column.name))
            self.columns.append(column.name)
        self.table = self.get_table()

    def get_table(self) -> str:
        return "Hallo!"
