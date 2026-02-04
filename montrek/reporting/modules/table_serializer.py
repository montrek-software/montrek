import pandas as pd
import datetime
from reporting.dataclasses import table_elements as te


class TableSerializer:
    """Handles serialization of table data to JSON format."""

    def __init__(self, table_elements):
        self.table_elements = table_elements

    def serialize_all(self, query_objects) -> list[dict]:
        """Serialize all query objects to a list of dictionaries."""
        return [self.serialize_object(obj) for obj in query_objects]

    def serialize_object(self, query_object) -> dict:
        """Convert a single query object to a dictionary."""
        result = {}

        for table_element in self.table_elements:
            if self._should_skip_element(table_element):
                continue

            key, value = self._serialize_element(table_element, query_object)
            result[key] = value

        return result

    def _should_skip_element(self, table_element) -> bool:
        """Check if table element should be skipped during serialization."""
        return isinstance(table_element, te.LinkTableElement)

    def _serialize_element(self, table_element, query_object) -> tuple[str, any]:
        """Extract key and serialized value from a table element."""
        raw_value = table_element.get_value(query_object)

        if isinstance(table_element, te.LinkTextTableElement):
            return table_element.text, str(raw_value)

        if isinstance(table_element, te.LinkListTableElement):
            return table_element.text, str([val[1] for val in raw_value])

        # Handle regular table elements
        return table_element.attr, self._format_value(raw_value, table_element)

    def _format_value(self, value, table_element):
        """Format a value based on its type."""
        if pd.isna(value):
            return None

        if isinstance(value, datetime.datetime | datetime.date):
            return value.isoformat()

        if isinstance(table_element, te.StringTableElement):
            return str(value)

        return value
