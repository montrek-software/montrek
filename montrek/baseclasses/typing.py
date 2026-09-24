import datetime
from typing import Any, ClassVar, Protocol

from django.db.models import QuerySet
from reporting.dataclasses.table_elements import TableElement

SessionDataType = dict[str, Any]
TableElementsType = list[TableElement] | tuple[TableElement, ...] | list | tuple
TableDataType = QuerySet | list[Any]


class ModelInstanceProtocol(Protocol):
    id: int


class ValueDateListProtocol(ModelInstanceProtocol):
    value_date: datetime.date | None


class MontrekHubProtocol(ModelInstanceProtocol):
    objects: ClassVar[Any]
    _meta: ClassVar[Any]


class HubValueDateProtocol(ModelInstanceProtocol):
    objects: ClassVar[Any]
    hub: MontrekHubProtocol
    value_date_list: ValueDateListProtocol
