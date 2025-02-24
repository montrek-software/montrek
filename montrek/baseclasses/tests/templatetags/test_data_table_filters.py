from unittest import mock
from dataclasses import dataclass
from django.test import TestCase
from django.urls import reverse
from reporting.dataclasses import table_elements
from baseclasses.templatetags.data_table_filters import (
    get_attribute,
    _get_dotted_attr_or_arg,
)


class TestShowItemFilterTests(TestCase):
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

    def test_get_attribute__none_value(self):
        self.obj["name"] = None
        result = get_attribute(self.obj, self.simple_element)
        self.assertIn("-", result)


@dataclass
class MockObject:
    name: str
    nested: dict


class TestShowItemFilterTestsObects(TestCase):
    def setUp(self):
        self.obj = MockObject(
            name="Test Name",
            nested={"value": "Nested Value"},
        )
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


class TestGetDottedAttrOrArgTests(TestCase):
    def test_get_dotted_attr_or_arg_dict(self):
        obj = {"level1": {"level2": "value"}}
        result = _get_dotted_attr_or_arg(obj, "level1.level2")
        self.assertEqual("value", result)

    def test_get_dotted_attr_or_arg_missing(self):
        obj = {"level1": {}}
        result = _get_dotted_attr_or_arg(obj, "level1.missing")
        self.assertIsNone(result)

    def test_get_dotted_attr_or_arg_obj(self):
        obj = MockObject(name="Test Name", nested={"value": "Nested Value"})
        result = _get_dotted_attr_or_arg(obj, "nested.value")
        self.assertEqual("Nested Value", result)


class TestGetLinkTests(TestCase):
    def setUp(self):
        self.obj = {
            "id": 1,
            "name": "Test",
            "list_attr": "1,2,3",
            "text_attr": "a,b,c",
            "sort_attr": "103,102,101",
        }
        shared_kwargs = {
            "url": "home",
            "kwargs": {},
            "hover_text": "Click me",
            "name": "link",
        }
        self.link_element = table_elements.LinkTableElement(
            icon="info",
            **shared_kwargs,
        )
        self.link_text_element = table_elements.LinkTextTableElement(
            text="Link Text",
            **shared_kwargs,
        )
        self.link_list_element = table_elements.LinkListTableElement(
            text="text_attr",
            list_attr="list_attr",
            list_kwarg="list_kwarg",
            sort_attr="sort_attr",
            **shared_kwargs,
        )

    def test_get_link_success(self):
        url = reverse("home")
        rendered_link = get_attribute(self.obj, self.link_element)
        self.assertIn(url, rendered_link)
        self.assertIn("Click me", rendered_link)

    def test_get_link_filter(self):
        url = reverse("home")
        self.link_element.kwargs = {"filter": "filter"}
        rendered_link = get_attribute(self.obj, self.link_element)
        self.assertIn(url, rendered_link)
        self.assertIn(
            "?filter_field=filter&amp;filter_lookup=in&amp;filter_value=None",
            rendered_link,
        )

    def test_get_text_link_success(self):
        url = reverse("home")
        rendered_link = get_attribute(self.obj, self.link_text_element)
        self.assertIn(url, rendered_link)
        self.assertIn("Click me", rendered_link)

    @mock.patch("baseclasses.templatetags.data_table_filters.reverse")
    def test_get_link_list_success(self, mock_reverse):
        def reverse_side_effect(*args, **kwargs):
            value = kwargs["kwargs"]["list_kwarg"]
            return f"/home/{value}"

        mock_reverse.side_effect = reverse_side_effect
        rendered_link = get_attribute(self.obj, self.link_list_element)
        self.assertEqual(
            rendered_link,
            (
                "<td>"
                '<a id="id__home_3" href="/home/3" title="Click me">c</a><br>'
                '<a id="id__home_2" href="/home/2" title="Click me">b</a><br>'
                '<a id="id__home_1" href="/home/1" title="Click me">a</a>'
                "</td>"
            ),
        )

    def test_get_link_no_reverse_match(self):
        self.link_element.url = "invalid_url"
        result = get_attribute(self.obj, self.link_element)
        self.assertEqual(result, "<td></td>")
