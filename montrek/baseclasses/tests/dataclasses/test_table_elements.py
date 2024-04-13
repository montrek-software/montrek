from django.utils import timezone
from django.test import TestCase
import baseclasses.dataclasses.table_elements as te

from reporting.core.reporting_colors import ReportingColors


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

    def test_data_quality_status_table_element(self):
        test_element = te.DataQualityStatusTableElement(name="test", attr="test_value")
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
