from django.test import TestCase
from baseclasses.templatetags import data_table_filters as dtf
from baseclasses.dataclasses import table_elements
from baseclasses.tests.factories.baseclass_factories import TestMontrekSatelliteFactory


class MockTableElement:
    def __init__(self, attr: str) -> None:
        self.attr = attr

    def format(self, value: str) -> str:
        return value


class TestDataTableFilters(TestCase):
    def test__get_dotted_attr_or_arg(self):
        """
        Test that the function returns the correct value when the
        attribute is a dotted path.
        """

        class TestClass:
            def __init__(self, attr):
                self.attr = attr

        test_obj = TestClass(attr="test_value")
        self.assertEqual(dtf._get_dotted_attr_or_arg(test_obj, "attr"), "test_value")

        class SecondTestClass:
            def __init__(self, attr):
                self.test_class = TestClass(attr=attr)

        second_test_obj = SecondTestClass(attr="test_value")
        self.assertEqual(
            dtf._get_dotted_attr_or_arg(second_test_obj, "test_class.attr"),
            "test_value",
        )
        self.assertEqual(dtf._get_dotted_attr_or_arg(test_obj, "no_attr"), None)

    def test__get_link_icon(self):
        test_obj = TestMontrekSatelliteFactory.create()
        table_element = table_elements.LinkTableElement(
            name="name",
            url="dummy_detail",
            kwargs={"pk": "pk"},
            icon="icon",
            hover_text="hover_text",
        )
        test_link = dtf._get_link(test_obj, table_element)
        self.assertEqual(
            str(test_link),
            f'<td><a id="id__baseclasses_{test_obj.id}_details" href="/baseclasses/{test_obj.id}/details" title="hover_text"><span class="glyphicon glyphicon-icon"></span></a></td>',
        )

    def test__get_link_text(self):
        test_obj = TestMontrekSatelliteFactory.create()
        table_element = table_elements.LinkTextTableElement(
            name="name",
            url="dummy_detail",
            kwargs={"pk": "pk"},
            text="test_name",
            hover_text="hover_text",
        )
        test_link = dtf._get_link(test_obj, table_element)
        self.assertEqual(
            str(test_link),
            f'<td><a id="id__baseclasses_{test_obj.id}_details" href="/baseclasses/{test_obj.id}/details" title="hover_text">{test_obj.test_name}</a></td>',
        )

    def test__get_link_text_filter(self):
        test_obj = TestMontrekSatelliteFactory.create()
        table_element = table_elements.LinkTextTableElement(
            name="name",
            url="dummy_detail",
            text="test_name",
            hover_text="hover_text",
            kwargs={"pk": "pk", "filter": "test_name"},
        )
        test_link = dtf._get_link(test_obj, table_element)
        self.assertTrue(
            f"?filter_field=test_name__in&amp;filter_value={test_obj.test_name}"
            in test_link
        )

    def test_get_attribute(self):
        test_obj = TestMontrekSatelliteFactory.create(test_name="Test Name")
        table_element = table_elements.LinkTableElement(
            name="name",
            url="dummy_detail",
            kwargs={"pk": "pk"},
            icon="icon",
            hover_text="hover_text",
        )
        test_str = dtf.get_attribute(test_obj, table_element)
        self.assertEqual(
            str(test_str),
            f'<td><a id="id__baseclasses_{test_obj.id}_details" href="/baseclasses/{test_obj.id}/details" title="hover_text"><span class="glyphicon glyphicon-icon"></span></a></td>',
        )
        table_element = table_elements.StringTableElement(
            name="name",
            attr="test_name",
        )
        test_str = dtf.get_attribute(test_obj, table_element)
        self.assertEqual(str(test_str), '<td style="text-align: left">Test Name</td>')

    def test_get_attribute__value_is_none(self):
        test_obj = TestMontrekSatelliteFactory.create(test_name="Test Name")
        for element_class in [
            table_elements.StringTableElement,
            table_elements.NumberTableElement,
        ]:
            table_element = element_class(
                name="name",
                attr="test_value",
            )
            test_str = dtf.get_attribute(test_obj, table_element)
            self.assertEqual(str(test_str), '<td style="text-align: center">-</td>')

    def test_get_attibute__object_is_dict(self):
        test_obj = {"test_name": "Test Name"}
        table_element = MockTableElement(
            attr="test_name",
        )
        test_str = dtf.get_attribute(test_obj, table_element)
        self.assertEqual(test_str, "Test Name")

    def test_get_attibute__object_is_dict_no_col(self):
        test_obj = {}
        table_element = MockTableElement(
            attr="test_name",
        )
        test_str = dtf.get_attribute(test_obj, table_element)
        self.assertEqual(test_str, "test_name")
