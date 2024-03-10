from django.test import TestCase
from baseclasses.managers.montrek_list_manager import MontrekListManager


class MockQuerySet:
    def __init__(self, *args):
        self.items = args

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def __eq__(self, other):
        if isinstance(other, list):
            return list(self.items) == other
        return NotImplemented

    def values(self):
        return [{item: item for item in self.items}]


class MockRepository:
    def __init__(self, session_data):
        self.session_data = session_data
        self.messages = []

    def std_queryset(self):
        return MockQuerySet("item1", "item2", "item3")  # Dummy data for testing


class MockHttpResponse:
    content: str = ""

    def write(self, content):
        self.content += content

    def getvalue(self):
        return self.content


class TestMontrekListManager(TestCase):
    def test_export_queryset_to_csv(self):
        manager = MontrekListManager()
        queryset = MockRepository({}).std_queryset()
        fields = ["item2", "field2", "item1"]
        response = manager.export_queryset_to_csv(queryset, fields, MockHttpResponse())
        self.assertEqual(
            response.getvalue(),
            "item2,field2,item1\r\nitem2,,item1\r\n",
        )
