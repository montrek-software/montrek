import datetime
from typing import Any, ClassVar, Protocol

from django.db.models import QuerySet

SessionDataType = dict[str, Any]
# Sequences of the table elements of the reporting app, which builds on this one.
TableElementsType = list[Any] | tuple[Any, ...]
TableDataType = QuerySet | list[Any]


class HtmlManagerProtocol(Protocol):
    def __init__(self, session_data: SessionDataType | None = None) -> None: ...

    def to_html(self) -> str: ...


class TableRowManagerProtocol(Protocol):
    """A table manager seen from a view that renders its rows."""

    live_rows_path: str

    def __init__(self, session_data: SessionDataType | None = None) -> None: ...

    @property
    def table_elements(self) -> TableElementsType: ...

    def get_full_table(self) -> TableDataType: ...

    def get_table_row(self, row_id: int) -> Any | None: ...

    def render_single_row(self, query_object: Any) -> str: ...

    def get_unsortable_fields(self) -> set[str]: ...


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
