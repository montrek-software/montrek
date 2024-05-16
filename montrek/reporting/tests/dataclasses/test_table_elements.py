from django.utils import timezone
from django.test import TestCase
import reporting.dataclasses.table_elements as te

from reporting.core.reporting_colors import ReportingColors
from baseclasses.tests.factories.baseclass_factories import TestMontrekSatelliteFactory


class TestTableElements(TestCase):
    def test_string_table_elements(self):
        test_element = te.StringTableElement(name="test", attr="test_value")
        self.assertEqual(
            test_element.format("test"), '<td style="text-align: left">test</td>'
        )
        self.assertEqual(
            test_element.format(1234), '<td style="text-align: left">1234</td>'
        )

    def test_float_table_elements(self):
        test_element = te.FloatTableElement(name="test", attr="test_value")
        self.assertEqual(
            test_element.format(1234.5678),
            '<td style="text-align:right;color:#002F6C;">1,234.568</td>',
        )
        self.assertEqual(
            test_element.format(1234),
            '<td style="text-align:right;color:#002F6C;">1,234.000</td>',
        )
        self.assertEqual(
            test_element.format(-1234),
            '<td style="text-align:right;color:#BE0D3E;">-1,234.000</td>',
        )
        self.assertEqual(
            test_element.format("bla"), '<td style="text-align:left;">bla</td>'
        )

    def test_euro_table_elements(self):
        test_element = te.EuroTableElement(name="test", attr="test_value")
        self.assertEqual(
            test_element.format(1234.5678),
            '<td style="text-align:right;color:#002F6C;">1,234.57&#x20AC;</td>',
        )
        self.assertEqual(
            test_element.format(1234),
            '<td style="text-align:right;color:#002F6C;">1,234.00&#x20AC;</td>',
        )
        self.assertEqual(
            test_element.format(-1234),
            '<td style="text-align:right;color:#BE0D3E;">-1,234.00&#x20AC;</td>',
        )
        self.assertEqual(
            test_element.format("bla"), '<td style="text-align:left;">bla</td>'
        )

    def test_dollar_table_elements(self):
        test_element = te.DollarTableElement(name="test", attr="test_value")
        self.assertEqual(
            test_element.format(1234.5678),
            '<td style="text-align:right;color:#002F6C;">1,234.57&#0036;</td>',
        )
        self.assertEqual(
            test_element.format(1234),
            '<td style="text-align:right;color:#002F6C;">1,234.00&#0036;</td>',
        )
        self.assertEqual(
            test_element.format(-1234),
            '<td style="text-align:right;color:#BE0D3E;">-1,234.00&#0036;</td>',
        )
        self.assertEqual(
            test_element.format("bla"), '<td style="text-align:left;">bla</td>'
        )

    def test_percent_table_elements(self):
        test_element = te.PercentTableElement(name="test", attr="test_value")
        self.assertEqual(
            test_element.format(0.2512),
            '<td style="text-align:right;color:#002F6C;">25.12%</td>',
        )
        self.assertEqual(
            test_element.format(1.234),
            '<td style="text-align:right;color:#002F6C;">123.40%</td>',
        )
        self.assertEqual(
            test_element.format(-0.1234),
            '<td style="text-align:right;color:#BE0D3E;">-12.34%</td>',
        )
        self.assertEqual(
            test_element.format("bla"), '<td style="text-align:left;">bla</td>'
        )

    def test_date_table_elements(self):
        test_element = te.DateTableElement(name="test", attr="test_value")
        self.assertEqual(
            test_element.format("2021-01-01"),
            '<td style="text-align:left;">2021-01-01</td>',
        )
        self.assertEqual(
            test_element.format("bla"), '<td style="text-align:left;">bla</td>'
        )
        self.assertEqual(
            test_element.format(timezone.datetime(2023, 12, 9)),
            '<td style="text-align:left;">09/12/2023</td>',
        )

    def test_bool_table_elements(self):
        test_element = te.BooleanTableElement(name="test", attr="test_value")
        self.assertEqual(
            test_element.format(True),
            '<td style="text-align:left;">&#x2713;</td>',
        )
        self.assertEqual(
            test_element.format(False),
            '<td style="text-align:left;">&#x2717;</td>',
        )
        self.assertEqual(
            test_element.format("bla"), '<td style="text-align:left;">&#x2713;</td>'
        )

    def test_not_implemented_table_elements(self):
        test_element = te.TableElement(name="test")
        with self.assertRaises(NotImplementedError):
            test_element.format("bla")

    def test_get_value_color(self):
        self.assertEqual(te._get_value_color(1), ReportingColors.DARK_BLUE)
        self.assertEqual(te._get_value_color(0), ReportingColors.DARK_BLUE)
        self.assertEqual(te._get_value_color(-2), ReportingColors.RED)

    def test_alert_table_element(self):
        test_element = te.AlertTableElement(name="test", attr="test_value")
        self.assertEqual(
            test_element.format("ok"),
            '<td style="text-align: left;color:#388E3C;">ok</td>',
        )
        self.assertEqual(
            test_element.format("warning"),
            '<td style="text-align: left;color:#FDD835;">warning</td>',
        )
        self.assertEqual(
            test_element.format("error"),
            '<td style="text-align: left;color:#BE0D3E;">error</td>',
        )

    def test_external_link_table_element(self):
        table_element = te.ExternalLinkTableElement(
            name="name",
            attr="test_attr",
        )
        test_str_html = table_element.format("https://www.google.com")
        self.assertEqual(
            str(test_str_html),
            '<td style="text-align:left;"><a href="https://www.google.com" title="https://www.google.com">https://www.google.com</a></td>',
        )


class MockTableElement(te.AttrTableElement):
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
        self.assertEqual(
            te.BaseLinkTableElement.get_dotted_attr_or_arg(test_obj, "attr"),
            "test_value",
        )

        class SecondTestClass:
            def __init__(self, attr):
                self.test_class = TestClass(attr=attr)

        second_test_obj = SecondTestClass(attr="test_value")
        self.assertEqual(
            te.BaseLinkTableElement.get_dotted_attr_or_arg(
                second_test_obj, "test_class.attr"
            ),
            "test_value",
        )
        self.assertEqual(
            te.BaseLinkTableElement.get_dotted_attr_or_arg(test_obj, "no_attr"), None
        )

    def test__get_link_icon(self):
        test_obj = TestMontrekSatelliteFactory.create()
        table_element = te.LinkTableElement(
            name="name",
            url="dummy_detail",
            kwargs={"pk": "pk"},
            icon="icon",
            hover_text="hover_text",
        )
        test_link = table_element.get_attribute(test_obj)
        self.assertEqual(
            str(test_link),
            f'<td><a id="id__baseclasses_{test_obj.id}_details" href="/baseclasses/{test_obj.id}/details" title="hover_text"><span class="glyphicon glyphicon-icon"></span></a></td>',
        )

    def test__get_link_text(self):
        test_obj = TestMontrekSatelliteFactory.create()
        table_element = te.LinkTextTableElement(
            name="name",
            url="dummy_detail",
            kwargs={"pk": "pk"},
            text="test_name",
            hover_text="hover_text",
        )
        test_link = table_element.get_attribute(test_obj)
        self.assertEqual(
            str(test_link),
            f'<td><a id="id__baseclasses_{test_obj.id}_details" href="/baseclasses/{test_obj.id}/details" title="hover_text">{test_obj.test_name}</a></td>',
        )

    def test__get_link_text_filter(self):
        test_obj = TestMontrekSatelliteFactory.create()
        table_element = te.LinkTextTableElement(
            name="name",
            url="dummy_detail",
            text="test_name",
            hover_text="hover_text",
            kwargs={"pk": "pk", "filter": "test_name"},
        )
        test_link = table_element.get_attribute(test_obj)
        self.assertTrue(
            f"?filter_field=test_name&filter_lookup=in&filter_value={test_obj.test_name}"
            in test_link
        )

    def test_get_attribute(self):
        test_obj = TestMontrekSatelliteFactory.create(test_name="Test Name")
        table_element = te.LinkTableElement(
            name="name",
            url="dummy_detail",
            kwargs={"pk": "pk"},
            icon="icon",
            hover_text="hover_text",
        )
        test_str = table_element.get_attribute(test_obj)
        self.assertEqual(
            str(test_str),
            f'<td><a id="id__baseclasses_{test_obj.id}_details" href="/baseclasses/{test_obj.id}/details" title="hover_text"><span class="glyphicon glyphicon-icon"></span></a></td>',
        )
        table_element = te.StringTableElement(
            name="name",
            attr="test_name",
        )
        test_str = table_element.get_attribute(test_obj)
        self.assertEqual(str(test_str), '<td style="text-align: left">Test Name</td>')

    def test_get_attribute__value_is_none(self):
        test_obj = TestMontrekSatelliteFactory.create(test_name="Test Name")
        for element_class in [
            te.StringTableElement,
            te.NumberTableElement,
        ]:
            table_element = element_class(
                name="name",
                attr="test_value",
            )
            test_str = table_element.get_attribute(test_obj)
            self.assertEqual(str(test_str), '<td style="text-align: center">-</td>')

    def test_get_attibute__object_is_dict(self):
        test_obj = {"test_name": "Test Name"}
        table_element = MockTableElement(
            attr="test_name",
        )
        test_str = table_element.get_attribute(test_obj)
        self.assertEqual(test_str, "Test Name")

    def test_get_attibute__object_is_dict_no_col(self):
        test_obj = {}
        table_element = MockTableElement(
            attr="test_name",
        )
        test_str = table_element.get_attribute(test_obj)
        self.assertEqual(test_str, "test_name")
