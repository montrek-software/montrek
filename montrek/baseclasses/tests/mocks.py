from dataclasses import dataclass


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

    def all(self):
        return self.items

    def count(self):
        return len(self.items)

    def get(self, pk):
        return self.items[pk]


@dataclass
class MockData:
    field: str
    value: int


@dataclass
class MockField:
    name: str


class MockObjects:
    def all(self):
        return MockQuerySet(
            MockData("item1", 1), MockData("item2", 2), MockData("item3", 3)
        )


class MockHub:
    objects = MockObjects()


class MockRepository:
    hub_class = MockHub

    def __init__(self, session_data):
        self.session_data = session_data
        self.messages = []
        self.annotations = {}

    def receive(self):
        return MockQuerySet(
            MockData("item1", 1), MockData("item2", 2), MockData("item3", 3)
        )  # Dummy data for testing

    def std_satellite_fields(self):
        return [
            MockField("item1"),
            MockField("item2"),
            MockField("item3"),
        ]  # Dummy data for testing

    def get_all_fields(self):
        return ["item1", "item2", "item3"]
