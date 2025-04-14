from typing import Any, Union
from reporting.dataclasses.table_elements import TableElement

SessionDataType = dict[str, Any]
TableElementsType = Union[list[TableElement], tuple[TableElement], list, tuple]
