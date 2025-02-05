from django.test import TestCase
from django.urls import reverse, NoReverseMatch
from reporting.dataclasses import table_elements
from baseclasses.templatetags.data_table_filters import (
    get_attribute,
    _get_dotted_attr_or_arg,
    _get_link,
)


class ShowItemFilterTests(TestCase):
    def setUp(self):
        self.obj = {
            "name": "Test Name",
            "nested": {"value": "Nested Value"},
        }
        self.simple_element = table_elements.TextTableElement(
            attr="name", name="simple"
        )
        self.nested_element = table_elements.TextTableElement(
            attr="nested.value", name="nested"
        )

    def test_get_attribute_simple(self):
        result = get_attribute(self.obj, self.simple_element)
        self.assertIn("Test Name", result)

    def test_get_attribute_nested(self):
        result = get_attribute(self.obj, self.nested_element)
        self.assertIn("nested.value", result)

    def test_get_attribute_missing(self):
        missing_element = table_elements.TextTableElement(
            attr="missing", name="missing"
        )
        result = get_attribute(self.obj, missing_element)
        self.assertIn("missing", result)  # Defaults to attribute name


class GetDottedAttrOrArgTests(TestCase):
    def test_get_dotted_attr_or_arg_dict(self):
        obj = {"level1": {"level2": "value"}}
        result = _get_dotted_attr_or_arg(obj, "level1.level2")
        self.assertEqual("value", result)

    def test_get_dotted_attr_or_arg_missing(self):
        obj = {"level1": {}}
        result = _get_dotted_attr_or_arg(obj, "level1.missing")
        self.assertIsNone(result)


class GetLinkTests(TestCase):
    def setUp(self):
        self.obj = {"id": 1, "name": "Test"}
        self.link_element = table_elements.LinkTableElement(
            url="home",
            kwargs={},
            icon="info",
            hover_text="Click me",
            name="link",
        )

    def test_get_link_success(self):
        # with self.settings(ROOT_URLCONF="your_project.urls"):
        url = reverse("home")
        rendered_link = _get_link(self.obj, self.link_element)
        self.assertIn(url, rendered_link)
        self.assertIn("Click me", rendered_link)

    def test_get_link_no_reverse_match(self):
        self.link_element.url = "invalid_url"
        result = _get_link(self.obj, self.link_element)
        self.assertEqual(result, "<td></td>")
