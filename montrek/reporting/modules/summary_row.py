import math
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from typing import Any

from reporting.dataclasses import table_elements as te
from reporting.dataclasses.display_field import DisplayField
from reporting.dataclasses.summary_row_config import SummaryRowConfig

Number = int | float | Decimal


class SummaryRow:
    """The summary row of a table: the label, and the sum of each summed column."""

    def __init__(
        self, config: SummaryRowConfig, table_elements: Sequence[te.TableElement]
    ):
        self.config = config
        self.table_elements = table_elements

    @property
    def summed_elements(self) -> list[te.NumberTableElement]:
        return [
            element
            for element in self.table_elements
            if isinstance(element, te.NumberTableElement)
            and element.summable
            and element.attr not in self.config.exclude_attrs
        ]

    @staticmethod
    def sum_rows(
        rows: Iterable[Any], elements: Sequence[te.NumberTableElement]
    ) -> list[Number | None]:
        """The sum of each element's values, in the order of the elements, as
        two columns may show the same field differently. Empty and non-numeric
        values are left out, and a column without any number sums to None, as
        SUM does."""
        totals: list[Number | None] = [None] * len(elements)
        for row in rows:
            for index, element in enumerate(elements):
                value = element.get_value(row)
                if not SummaryRow._is_number(value):
                    continue
                total = totals[index]
                totals[index] = value if total is None else total + value
        return totals

    @staticmethod
    def _is_number(value: Any) -> bool:
        if isinstance(value, bool) or not isinstance(value, Number):
            return False
        return not (isinstance(value, float) and math.isnan(value))

    def display_fields(self, sums: Sequence[Any]) -> list[DisplayField]:
        """``sums`` holds the total of each of ``summed_elements``, in order."""
        summed_elements = self.summed_elements
        totals = {
            id(element): total
            for element, total in zip(summed_elements, sums, strict=True)
        }
        summed = {id(element): element for element in summed_elements}
        label_index = self._label_index(summed)
        fields = []
        for index, element in enumerate(self.table_elements):
            summed_element = summed.get(id(element))
            total = totals.get(id(element))
            if summed_element is not None and total is not None:
                fields.append(summed_element.get_sum_display_field(total))
            elif index == label_index:
                fields.append(self._cell(element, str(self.config.label)))
            else:
                fields.append(self._cell(element, ""))
        return fields

    def _label_index(self, summed: Mapping[int, te.NumberTableElement]) -> int | None:
        for index, element in enumerate(self.table_elements):
            if self.config.label_attr:
                if element.field_name == self.config.label_attr:
                    return index
            elif id(element) not in summed:
                return index
        return None

    @staticmethod
    def _cell(element: te.TableElement, display_value: str) -> DisplayField:
        return DisplayField(
            name=element.name,
            display_value=display_value,
            style_attrs_str="",
            td_classes_str="text-start",
            hover_text=None,
            value=None,
        )
