import datetime
from unittest.mock import Mock
from django.test import TestCase
import pandas as pd
from reporting.dataclasses import table_elements as te

from reporting.modules.table_serializer import TableSerializer


class TableSerializerTestCase(TestCase):
    """Test suite for TableSerializer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.query_object = Mock()

    def test_serialize_all_with_empty_list(self):
        """Test serializing an empty list of query objects."""
        serializer = TableSerializer([])
        result = serializer.serialize_all([])

        self.assertEqual(result, [])

    def test_serialize_all_with_multiple_objects(self):
        """Test serializing multiple query objects."""
        element = Mock(spec=te.StringTableElement)
        element.attr = "name"
        element.get_value.side_effect = lambda obj: f"value_{id(obj)}"

        serializer = TableSerializer([element])
        obj1, obj2 = Mock(), Mock()
        result = serializer.serialize_all([obj1, obj2])

        self.assertEqual(len(result), 2)
        self.assertIn("name", result[0])
        self.assertIn("name", result[1])

    def test_skip_link_table_element(self):
        """Test that LinkTableElement is skipped during serialization."""
        link_element = Mock(spec=te.LinkTableElement)
        regular_element = Mock(spec=te.StringTableElement)
        regular_element.attr = "field"
        regular_element.get_value.return_value = "value"

        serializer = TableSerializer([link_element, regular_element])
        result = serializer.serialize_object(self.query_object)

        self.assertNotIn("link", result)
        self.assertIn("field", result)
        link_element.get_value.assert_not_called()

    def test_serialize_link_text_table_element(self):
        """Test serialization of LinkTextTableElement."""
        element = Mock(spec=te.LinkTextTableElement)
        element.text = "link_text"
        element.get_value.return_value = "http://example.com"

        serializer = TableSerializer([element])
        result = serializer.serialize_object(self.query_object)

        self.assertEqual(result["link_text"], "http://example.com")
        element.get_value.assert_called_once_with(self.query_object)

    def test_serialize_link_list_table_element(self):
        """Test serialization of LinkListTableElement."""
        element = Mock(spec=te.LinkListTableElement)
        element.text = "links"
        element.get_value.return_value = [
            ("id1", "Link 1"),
            ("id2", "Link 2"),
            ("id3", "Link 3"),
        ]

        serializer = TableSerializer([element])
        result = serializer.serialize_object(self.query_object)

        self.assertEqual(result["links"], "['Link 1', 'Link 2', 'Link 3']")

    def test_serialize_string_table_element(self):
        """Test serialization of StringTableElement."""
        element = Mock(spec=te.StringTableElement)
        element.attr = "description"
        element.get_value.return_value = 123  # Non-string value

        serializer = TableSerializer([element])
        result = serializer.serialize_object(self.query_object)

        self.assertEqual(result["description"], "123")
        self.assertIsInstance(result["description"], str)

    def test_format_value_with_none(self):
        """Test formatting of NaN values to None."""
        element = Mock()
        element.attr = "field"
        element.get_value.return_value = pd.NA

        serializer = TableSerializer([element])
        result = serializer.serialize_object(self.query_object)

        self.assertIsNone(result["field"])

    def test_format_value_with_datetime(self):
        """Test formatting of datetime values to ISO format."""
        element = Mock()
        element.attr = "created_at"
        test_datetime = datetime.datetime(2024, 1, 15, 10, 30, 45)
        element.get_value.return_value = test_datetime

        serializer = TableSerializer([element])
        result = serializer.serialize_object(self.query_object)

        self.assertEqual(result["created_at"], "2024-01-15T10:30:45")

    def test_format_value_with_date(self):
        """Test formatting of date values to ISO format."""
        element = Mock()
        element.attr = "birth_date"
        test_date = datetime.date(2024, 1, 15)
        element.get_value.return_value = test_date

        serializer = TableSerializer([element])
        result = serializer.serialize_object(self.query_object)

        self.assertEqual(result["birth_date"], "2024-01-15")

    def test_format_value_preserves_regular_types(self):
        """Test that regular types (int, float, bool) are preserved."""
        int_element = Mock()
        int_element.attr = "count"
        int_element.get_value.return_value = 42

        float_element = Mock()
        float_element.attr = "price"
        float_element.get_value.return_value = 19.99

        bool_element = Mock()
        bool_element.attr = "active"
        bool_element.get_value.return_value = True

        serializer = TableSerializer([int_element, float_element, bool_element])
        result = serializer.serialize_object(self.query_object)

        self.assertEqual(result["count"], 42)
        self.assertIsInstance(result["count"], int)
        self.assertEqual(result["price"], 19.99)
        self.assertIsInstance(result["price"], float)
        self.assertEqual(result["active"], True)
        self.assertIsInstance(result["active"], bool)

    def test_serialize_mixed_table_elements(self):
        """Test serialization with a mix of different table element types."""
        link_skip = Mock(spec=te.LinkTableElement)

        link_text = Mock(spec=te.LinkTextTableElement)
        link_text.text = "url"
        link_text.get_value.return_value = "http://test.com"

        link_list = Mock(spec=te.LinkListTableElement)
        link_list.text = "related"
        link_list.get_value.return_value = [("1", "Item 1"), ("2", "Item 2")]

        string_elem = Mock(spec=te.StringTableElement)
        string_elem.attr = "name"
        string_elem.get_value.return_value = "Test Name"

        date_elem = Mock()
        date_elem.attr = "updated"
        date_elem.get_value.return_value = datetime.date(2024, 2, 1)

        serializer = TableSerializer(
            [link_skip, link_text, link_list, string_elem, date_elem]
        )
        result = serializer.serialize_object(self.query_object)

        self.assertEqual(len(result), 4)  # link_skip is excluded
        self.assertEqual(result["url"], "http://test.com")
        self.assertEqual(result["related"], "['Item 1', 'Item 2']")
        self.assertEqual(result["name"], "Test Name")
        self.assertEqual(result["updated"], "2024-02-01")

    def test_serialize_object_with_no_elements(self):
        """Test serialization with no table elements."""
        serializer = TableSerializer([])
        result = serializer.serialize_object(self.query_object)

        self.assertEqual(result, {})

    def test_format_value_with_numpy_nan(self):
        """Test formatting of numpy NaN values."""
        element = Mock()
        element.attr = "score"
        element.get_value.return_value = float("nan")

        serializer = TableSerializer([element])
        result = serializer.serialize_object(self.query_object)

        self.assertIsNone(result["score"])
