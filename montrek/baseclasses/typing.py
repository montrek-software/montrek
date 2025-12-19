from datetime import datetime
from typing import Any, Optional, Protocol, Union

from django.db import models
from reporting.dataclasses.table_elements import TableElement

SessionDataType = dict[str, Any]
TableElementsType = Union[list[TableElement], tuple[TableElement], list, tuple]


class ModelInstanceProtocol(Protocol):
    id: int


class ValueDateListProtocol(ModelInstanceProtocol):
    value_date: Optional[datetime.date]


class MontrekHubProtocol(ModelInstanceProtocol):
    hub_value_date: models.Model
