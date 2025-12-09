from typing import ClassVar

from django.test import TestCase
from reporting.dataclasses.display_field import DisplayField
from reporting.dataclasses.table_elements import TableElement


class MockTableElement(TableElement):
    style_attrs: ClassVar[dict[str, str]] = {"mock": "flock", "sock": "rock"}


class TestDisplayField(TestCase):
    def test_style_attrs_str(self):
        display_field = DisplayField(
            value="123", table_element=MockTableElement(name="test")
        )
        self.assertEqual(display_field.style_attrs_str, "mock: flock; sock: rock;")
