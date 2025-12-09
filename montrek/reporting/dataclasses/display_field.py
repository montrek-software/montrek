from dataclasses import dataclass
from typing import Any

from reporting.dataclasses.table_elements import TableElement


@dataclass
class DisplayField:
    table_element: TableElement
    value: Any

    @property
    def display_value(self) -> str:
        return self.table_element.format(self.value)

    @property
    def style_attrs_str(self) -> str:
        return self.table_element.get_style_attrs_str(self.value)

    @property
    def td_classes_str(self) -> str:
        return self.table_element.get_td_classes_str(self.value)
