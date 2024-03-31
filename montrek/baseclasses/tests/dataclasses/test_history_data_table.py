from django.test import TestCase
from baseclasses.dataclasses.history_data_table import HistoryDataTable


class MockField:
    def __init__(self, name):
        self.name = name


class MockModel:
    class _meta:
        fields = [MockField("field_1"), MockField("field_2")]


class MockQueryset:
    model = MockModel()


class TestHistoryDataTable(TestCase):
    def test_history_data_table(self):
        history_data_table = HistoryDataTable(
            title="test_title", queryset=MockQueryset()
        )
        elements = history_data_table.elements
        self.assertEqual(elements[0].name, "field_1")
        self.assertEqual(elements[1].name, "field_2")
        self.assertEqual(elements[0].attr, "field_1")
        self.assertEqual(elements[1].attr, "field_2")
