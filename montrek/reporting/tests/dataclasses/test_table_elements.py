import datetime
from dataclasses import dataclass
from decimal import Decimal
from functools import wraps
from typing import Any, Protocol
from unittest import mock

import reporting.dataclasses.table_elements as te
import requests
from baseclasses.tests.factories.baseclass_factories import TestMontrekSatelliteFactory
from django.test import TestCase
from reporting.core.reporting_colors import ReportingColors


class MockTableElement(te.AttrTableElement):
    def __init__(self, attr: str) -> None:
        self.attr = attr

    def format(self, value: str) -> str:
        return value


class MockTableElementCustomHoverText(te.StringTableElement):
    def get_hover_text(self, obj: Any) -> str | None:
        return f"Hover from field {obj[str(self.hover_text)]}"


class MockActiveLinkTableElement(te.LinkTextTableElement):
    def is_active(self, value: Any, obj: Any) -> bool:
        if value == "is_active":
            return True
        if value == "is_not_active":
            return False
        return obj["is_active"]


class HasAssertEqual(Protocol):
    def assertEqual(self, first, second, msg=None): ...
    def subTest(self, msg="", **params) -> Any: ...


class TableElementTestingToolMixin(HasAssertEqual):
    def table_element_test_assertions_from_value(
        self,
        table_element: te.AttrTableElement,
        value: Any,
        expected_format: str,
        expected_format_latex: str,
        expected_style_attrs: te.style_attrs_type = {},
        expected_td_classes: te.td_classes_type = ["text-start"],
        expected_hover_text: str | None = None,
        expected_none_hover_text: str | None = None,
    ):
        test_obj = {table_element.attr: value}
        self.table_element_test_assertions_from_object(
            table_element,
            test_obj,
            expected_format,
            expected_format_latex,
            expected_style_attrs,
            expected_td_classes,
            expected_hover_text,
        )
        with self.subTest("Test None Representation"):
            if value is not None:
                if expected_none_hover_text is None:
                    expected_none_hover_text = expected_hover_text
                self.table_element_test_assertions_from_value(
                    table_element=table_element,
                    value=None,
                    expected_format="-",
                    expected_format_latex=" \\color{black} - &",
                    expected_td_classes=["text-center"],
                    expected_hover_text=expected_none_hover_text,
                )

    def table_element_test_assertions_from_object(
        self,
        table_element: te.TableElement,
        test_obj: Any,
        expected_format: str,
        expected_format_latex: str,
        expected_style_attrs: te.style_attrs_type = {},
        expected_td_classes: te.td_classes_type = ["text-start"],
        expected_hover_text: str | None = None,
    ):
        with self.subTest("Test HTML Representation"):
            self.assert_display_field_properties(
                table_element,
                test_obj,
                expected_format,
                expected_style_attrs,
                expected_td_classes,
                expected_hover_text,
            )

        with self.subTest("Test Latex Representation"):
            self.assertEqual(
                table_element.get_attribute(test_obj, "latex"), expected_format_latex
            )

    def assert_display_field_properties(
        self,
        table_element: te.TableElement,
        obj: Any,
        expected_format: str,
        expected_style_attrs: te.style_attrs_type = {},
        expected_td_classes: te.td_classes_type = ["text-start"],
        expected_hover_text: str | None = None,
    ):
        test_display_field = table_element.get_display_field(obj)
        self.assertEqual(test_display_field.name, table_element.name)
        self.assertEqual(
            test_display_field.display_value.replace("\n", "").lstrip(),
            expected_format.replace("\n", "").lstrip(),
        )
        self.assertEqual(test_display_field.hover_text, expected_hover_text)
        self.assertEqual(
            test_display_field.td_classes_str, " ".join(expected_td_classes)
        )
        if len(expected_style_attrs) > 0:
            self.assertEqual(
                test_display_field.style_attrs_str,
                "; ".join(f"{k}: {v}" for k, v in expected_style_attrs.items()) + ";",
            )
        else:
            self.assertEqual(test_display_field.style_attrs_str, "")


class TestTableElements(TestCase, TableElementTestingToolMixin):
    def test_string_table_elements(self):
        test_element = te.StringTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="test",
            expected_format="test",
            expected_format_latex=" \\color{black} test &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1234,
            expected_format="1234",
            expected_format_latex=" \\color{black} 1234 &",
        )

    def test_string_table_elements_with_hover_text(self):
        test_element = te.StringTableElement(
            name="test", attr="test_value", hover_text="Hallo"
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="test",
            expected_format="test",
            expected_format_latex=" \\color{black} test &",
            expected_hover_text="Hallo",
        )

    def test_string_table_elements_with_custom_hover_text(self):
        test_element = MockTableElementCustomHoverText(
            name="test", attr="test_value", hover_text="field2"
        )
        self.table_element_test_assertions_from_object(
            table_element=test_element,
            test_obj={"test_value": "test", "field2": "Hallo"},
            expected_format="test",
            expected_format_latex=" \\color{black} test &",
            expected_hover_text="Hover from field Hallo",
        )

    def test_text_table_element(self):
        test_element = te.TextTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="test",
            expected_format="test",
            expected_format_latex=" \\color{black} test &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1234,
            expected_format="1234",
            expected_format_latex=" \\color{black} 1234 &",
        )

    def test_secure_table_element(self):
        test_element = te.TextTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="<script>Malicious Hack</script><button>Here</button>",
            expected_format="Malicious HackHere",
            expected_format_latex=" \\color{black} Malicious HackHere &",
        )

    def test_list_table_element(self):
        test_element = te.ListTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="test1,test2",
            expected_format="test1<br>    test2",
            expected_format_latex=" \\color{black} test1,test2 &",
        )

        test_element = te.ListTableElement(
            name="test", attr="test_value", in_separator=";", out_separator="|"
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="test1,2;test2;test4",
            expected_format="test1,2|    test2|    test4",
            expected_format_latex=" \\color{black} test1,2;test2;test4 &",
        )

    def test_float_table_elements(self):
        test_element = te.FloatTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1234.5678,
            expected_format="1,234.568",
            expected_format_latex="\\color{darkblue} 1,234.568 &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=Decimal(1234.5678),
            expected_format="1,234.568",
            expected_format_latex="\\color{darkblue} 1,234.568 &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1234,
            expected_format="1,234.000",
            expected_format_latex="\\color{darkblue} 1,234.000 &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=-1234,
            expected_format="-1,234.000",
            expected_format_latex="\\color{red} -1,234.000 &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#BE0D3E"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="bla",
            expected_format="bla",
            expected_format_latex="bla &",
            expected_td_classes=["text-start"],
        )

    def test_int_table_elements(self):
        test_element = te.IntTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1234.5678,
            expected_format="1,234",
            expected_format_latex="\\color{darkblue} 1,234 &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.assertEqual(test_element.get_value({"test_value": 1234.56}), 1234)
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=Decimal(1234.5678),
            expected_format="1,234",
            expected_format_latex="\\color{darkblue} 1,234 &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1234,
            expected_format="1,234",
            expected_format_latex="\\color{darkblue} 1,234 &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="1234",
            expected_format="1,234",
            expected_format_latex="\\color{darkblue} 1,234 &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=-1234,
            expected_format="-1,234",
            expected_format_latex="\\color{red} -1,234 &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#BE0D3E"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="bla",
            expected_format="bla",
            expected_format_latex="bla &",
            expected_td_classes=["text-start"],
        )

    def test_euro_table_elements(self):
        test_element = te.EuroTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1234.5678,
            expected_format="1,234.57€",
            expected_format_latex="\\color{darkblue} 1,234.57€ &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1234,
            expected_format="1,234.00€",
            expected_format_latex="\\color{darkblue} 1,234.00€ &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=-1234,
            expected_format="-1,234.00€",
            expected_format_latex="\\color{red} -1,234.00€ &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#BE0D3E"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="bla",
            expected_format="bla€",
            expected_format_latex="bla€ &",
            expected_td_classes=["text-start"],
        )

    def test_dollar_table_elements(self):
        test_element = te.DollarTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1234.5678,
            expected_format="1,234.57$",
            expected_format_latex="\\color{darkblue} 1,234.57\\$ &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1234,
            expected_format="1,234.00$",
            expected_format_latex="\\color{darkblue} 1,234.00\\$ &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=-1234,
            expected_format="-1,234.00$",
            expected_format_latex="\\color{red} -1,234.00\\$ &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#BE0D3E"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="bla",
            expected_format="bla$",
            expected_format_latex="bla\\$ &",
            expected_td_classes=["text-start"],
        )

    def test_percent_table_elements(self):
        test_element = te.PercentTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=0.2512,
            expected_format="25.12%",
            expected_format_latex="\\color{darkblue} 25.12\\% &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=1.234,
            expected_format="123.40%",
            expected_format_latex="\\color{darkblue} 123.40\\% &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=-1.234,
            expected_format="-123.40%",
            expected_format_latex="\\color{red} -123.40\\% &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#BE0D3E"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="bla",
            expected_format="bla",
            expected_format_latex="bla &",
            expected_td_classes=["text-start"],
        )

    def test_date_table_elements(self):
        test_element = te.DateTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="2021-01-01",
            expected_format="2021-01-01",
            expected_format_latex=" \\color{black} 2021-01-01 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="01.01.2021",
            expected_format="2021-01-01",
            expected_format_latex=" \\color{black} 2021-01-01 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=datetime.date(2021, 1, 1),
            expected_format="2021-01-01",
            expected_format_latex=" \\color{black} 2021-01-01 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=datetime.datetime(2021, 1, 1, 12, 48),
            expected_format="2021-01-01",
            expected_format_latex=" \\color{black} 2021-01-01 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="bla",
            expected_format="bla",
            expected_format_latex=" \\color{black} bla &",
            expected_td_classes=["text-start"],
        )

    def test_date_german_table_elements(self):
        test_element = te.DateGermanTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="2021-01-01",
            expected_format="01.01.2021",
            expected_format_latex=" \\color{black} 01.01.2021 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="01.01.2021",
            expected_format="01.01.2021",
            expected_format_latex=" \\color{black} 01.01.2021 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=datetime.date(2021, 1, 1),
            expected_format="01.01.2021",
            expected_format_latex=" \\color{black} 01.01.2021 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=datetime.datetime(2021, 1, 1, 12, 48),
            expected_format="01.01.2021",
            expected_format_latex=" \\color{black} 01.01.2021 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="bla",
            expected_format="bla",
            expected_format_latex=" \\color{black} bla &",
            expected_td_classes=["text-start"],
        )

    def test_date_time_table_elements(self):
        test_element = te.DateTimeTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="2021-01-01",
            expected_format="2021-01-01 00:00:00",
            expected_format_latex=" \\color{black} 2021-01-01 00:00:00 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="01.01.2021",
            expected_format="2021-01-01 00:00:00",
            expected_format_latex=" \\color{black} 2021-01-01 00:00:00 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=datetime.date(2021, 1, 1),
            expected_format="2021-01-01 00:00:00",
            expected_format_latex=" \\color{black} 2021-01-01 00:00:00 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=datetime.datetime(2021, 1, 1, 12, 48),
            expected_format="2021-01-01 12:48:00",
            expected_format_latex=" \\color{black} 2021-01-01 12:48:00 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="bla",
            expected_format="bla",
            expected_format_latex=" \\color{black} bla &",
            expected_td_classes=["text-start"],
        )

    def test_date_year_table_elements(self):
        test_element = te.DateYearTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="2021-01-01",
            expected_format="2021",
            expected_format_latex=" \\color{black} 2021 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="01.01.2021",
            expected_format="2021",
            expected_format_latex=" \\color{black} 2021 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=datetime.date(2021, 1, 1),
            expected_format="2021",
            expected_format_latex=" \\color{black} 2021 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=datetime.datetime(2021, 1, 1, 12, 48),
            expected_format="2021",
            expected_format_latex=" \\color{black} 2021 &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="bla",
            expected_format="bla",
            expected_format_latex=" \\color{black} bla &",
            expected_td_classes=["text-start"],
        )

    def test_bool_table_elements(self):
        test_element = te.BooleanTableElement(name="test", attr="test_value")
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=True,
            expected_format='    <span class="bi bi-check-circle-fill text-success"></span>',
            expected_format_latex="\\twemoji{white_check_mark} &",
            expected_td_classes=["text-center"],
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value=False,
            expected_format='    <span class="bi bi-x-circle-fill text-danger"></span>',
            expected_format_latex="\\twemoji{cross mark} &",
            expected_td_classes=["text-center"],
        )

    def test_wrap_text_in_string_table_element(self):
        test_obj = TestMontrekSatelliteFactory.create(test_text="Test Name" * 20)
        table_element = te.StringTableElement(
            name="name",
            attr="test_text",
        )
        value = table_element.get_display_field(test_obj).display_value
        self.assertIn("<br>", value)

    def test_wrap_text_in_string_table_element__none(self):
        test_obj = TestMontrekSatelliteFactory.create()
        table_element = te.StringTableElement(
            name="name",
            attr="test_value",
        )
        value = table_element.get_value(test_obj)
        self.assertEqual(None, value)

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
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="ok",
            expected_format="<b>ok</b>",
            expected_format_latex=" \\color{black} ok &",
            expected_td_classes=["text-center"],
            expected_style_attrs={"color": "#388E3C"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="warning",
            expected_format="<b>warning</b>",
            expected_format_latex=" \\color{black} warning &",
            expected_td_classes=["text-center"],
            expected_style_attrs={"color": "#FDD835"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="error",
            expected_format="<b>error</b>",
            expected_format_latex=" \\color{black} error &",
            expected_td_classes=["text-center"],
            expected_style_attrs={"color": "#BE0D3E"},
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="bla",
            expected_format="<b>bla</b>",
            expected_format_latex=" \\color{black} bla &",
            expected_td_classes=["text-center"],
            expected_style_attrs={"color": "#000000"},
        )

    def test_external_link_table_element__html(self):
        test_element = te.ExternalLinkTableElement(
            name="name",
            attr="test_attr",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="https://www.google.com",
            expected_format='<a href="https://www.google.com" target="_blank">https://www.google.com</a>',
            expected_format_latex=" \\url{https://www.google.com} &",
            expected_hover_text="https://www.google.com",
            expected_none_hover_text="No link",
        )

    def test_latex_special_character_is_handled(self):
        table_element = te.StringTableElement(
            name="name",
            attr="test_attr",
        )
        test_str_latex = table_element.format_latex("this & that = 100%")
        self.assertEqual(
            test_str_latex,
            " \\color{black} this \\& that = 100\\% &",
        )

    def test_external_link_table_element__latex(self):
        table_element = te.ExternalLinkTableElement(
            name="name",
            attr="test_attr",
        )
        test_str_latex = table_element.format_latex("https://www.google.com")
        self.assertEqual(
            test_str_latex,
            " \\url{https://www.google.com} &",
        )

    def test_image_table_element(self):
        table_element = te.ImageTableElement(
            name="name",
            attr="test_attr",
        )
        self.table_element_test_assertions_from_value(
            table_element=table_element,
            value="pic.png",
            expected_format='<img src="pic.png" alt="image" width="100" height="100">',
            expected_format_latex="\\includegraphics[width=0.3\\textwidth]{pic.png} &",
        )
        table_element = te.ImageTableElement(
            name="name", attr="test_attr", alt="alt_image"
        )
        self.table_element_test_assertions_from_value(
            table_element=table_element,
            value="pic.png",
            expected_format='<img src="pic.png" alt="alt_image" width="100" height="100">',
            expected_format_latex="\\includegraphics[width=0.3\\textwidth]{pic.png} &",
        )

    def test_image_table_element__latex_image(self):
        table_element = te.ImageTableElement(
            name="name",
            attr="test_attr",
        )
        test_str = table_element.format_latex("pic.png")
        self.assertEqual(
            test_str,
            "\\includegraphics[width=0.3\\textwidth]{pic.png} &",
        )

    def test_image_table_element__latex_url(self):
        table_element = te.ImageTableElement(
            name="name",
            attr="test_attr",
        )
        url = "https://upload.wikimedia.org/wikipedia/commons/7/70/Example.png"
        fake_response = mock.Mock()
        fake_response.status_code = 200
        fake_response.content = b"fake image bytes"

        with mock.patch.object(requests, "get", return_value=fake_response):
            test_str_latex = table_element.format_latex(url)
        self.assertIn(
            "\\includegraphics[width=0.3\\textwidth]{/tmp/",
            test_str_latex,
        )
        self.assertIn(
            ".png} &",
            test_str_latex,
        )

    def test_image_table_element__latex_url_not_found(self):
        table_element = te.ImageTableElement(
            name="name",
            attr="test_attr",
        )
        url = "https://upload.wikimedia.org/dummy.png"
        test_str_latex = table_element.format_latex(url)
        self.assertEqual(
            test_str_latex,
            f"Image not found: {url} &",
        )

    def test_method_name_table_element(self):
        def my_decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        class Functions:
            def do_nothing(self):
                pass

            @staticmethod
            def return_one(arg1: str, arg2: int) -> int:
                """
                Returns 1.

                Parameters:
                arg1 (str): The first argument.
                arg2 (int): The second argument.

                Returns:
                int: 1
                """
                return 1

            @classmethod
            @my_decorator
            def return_two(cls) -> int:
                """Returns 2."""
                return 2

        test_element = te.MethodNameTableElement(
            name="name", attr="function_name", class_=Functions
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="do_nothing",
            expected_format='<div title="">do_nothing</div>',
            expected_format_latex=" \\color{black} do\\_nothing &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="return_one",
            expected_format='<div title="Returns 1.\n\nParameters:\narg1 (str): The first argument.\narg2 (int): The second argument.\n\nReturns:\nint: 1">return_one</div>',
            expected_format_latex=" \\color{black} return\\_one &",
        )
        self.table_element_test_assertions_from_value(
            table_element=test_element,
            value="return_two",
            expected_format='<div title="Returns 2.">return_two</div>',
            expected_format_latex=" \\color{black} return\\_two &",
        )

    @mock.patch("reporting.dataclasses.table_elements.reverse")
    def test_link_list_table_element(self, mock_reverse):
        fake_url = "fake_url"

        def reverse_side_effect(*args, **kwargs):
            value = kwargs["kwargs"]["list_kwarg"]
            return f"/{fake_url}/{value}"

        mock_reverse.side_effect = reverse_side_effect
        test_element = te.LinkListTableElement(
            name="name",
            url=fake_url,
            hover_text="hover_text",
            text="text_attr",
            kwargs={},
            list_attr="list_attr",
            list_kwarg="list_kwarg",
            in_separator=",",
        )
        obj = {"list_attr": "1,2,3", "text_attr": "a,b,c"}
        self.table_element_test_assertions_from_object(
            table_element=test_element,
            test_obj=obj,
            expected_format='<div style="max-height: 300px; overflow-y: auto;">      <div><a id="id__fake_url_1" href="/fake_url/1">a</a></div>      <div><a id="id__fake_url_2" href="/fake_url/2">b</a></div>      <div><a id="id__fake_url_3" href="/fake_url/3">c</a></div>  </div>',
            expected_format_latex=" \\color{black} a,b,c &",
            expected_hover_text="hover_text",
        )

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

    def test__get_link_text(self):
        test_obj = TestMontrekSatelliteFactory.create()
        test_element = te.LinkTextTableElement(
            name="name",
            url="dummy_detail",
            kwargs={"pk": "pk"},
            text="test_name",
            hover_text="hover_text",
        )
        self.table_element_test_assertions_from_object(
            table_element=test_element,
            test_obj=test_obj,
            expected_format=f'<a id="id__baseclasses_{test_obj.id}_details" href="/baseclasses/{test_obj.id}/details">{test_obj.test_name}</a>',
            expected_format_latex=f" \\color{{black}} {test_obj.test_name} &",
            expected_hover_text="hover_text",
        )

    def test__get_link_text__active(self):
        test_element = MockActiveLinkTableElement(
            name="name",
            url="dummy_detail",
            kwargs={"pk": "pk"},
            text="test_name",
            hover_text="hover_text",
        )
        test_obj = {"pk": 1, "test_name": "Test_Name", "is_active": False}
        self.table_element_test_assertions_from_object(
            table_element=test_element,
            test_obj=test_obj,
            expected_format='<a id="id__baseclasses_1_details" href="/baseclasses/1/details">Test_Name</a>',
            expected_format_latex=" \\color{black} Test\\_Name &",
            expected_hover_text="hover_text",
        )
        test_obj = {"pk": 1, "test_name": "Test_Name", "is_active": True}
        self.table_element_test_assertions_from_object(
            table_element=test_element,
            test_obj=test_obj,
            expected_format='<a id="id__baseclasses_1_details" href="/baseclasses/1/details">Test_Name</a>',
            expected_format_latex=" \\color{black} Test\\_Name &",
            expected_hover_text="hover_text",
            expected_td_classes=["text-start fw-bold"],
        )
        test_obj = {"pk": 1, "test_name": "is_active", "is_active": False}
        self.table_element_test_assertions_from_object(
            table_element=test_element,
            test_obj=test_obj,
            expected_format='<a id="id__baseclasses_1_details" href="/baseclasses/1/details">is_active</a>',
            expected_format_latex=" \\color{black} is\\_active &",
            expected_hover_text="hover_text",
            expected_td_classes=["text-start fw-bold"],
        )
        test_obj = {"pk": 1, "test_name": "is_not_active", "is_active": True}
        self.table_element_test_assertions_from_object(
            table_element=test_element,
            test_obj=test_obj,
            expected_format='<a id="id__baseclasses_1_details" href="/baseclasses/1/details">is_not_active</a>',
            expected_format_latex=" \\color{black} is\\_not\\_active &",
            expected_hover_text="hover_text",
            expected_td_classes=["text-start"],
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
        test_display_field = table_element.get_display_field(test_obj)
        test_link = test_display_field.display_value
        self.assertTrue(
            f"?filter_field=test_name&amp;filter_lookup=in&amp;filter_value={test_obj.test_name}"
            in test_link
        )

    def test__get_link_static_kwargs(self):
        test_obj = TestMontrekSatelliteFactory.create()
        table_element = te.LinkTextTableElement(
            name="name",
            url="dummy_detail_static",
            text="test_name",
            hover_text="hover_text",
            kwargs={"pk": "pk", "filter": "test_name"},
            static_kwargs={"static": "test_static"},
        )
        test_kwargs = table_element.get_url_kwargs(test_obj)
        self.assertEqual(test_kwargs["static"], "test_static")

    def test_link_icon(self):
        test_obj = TestMontrekSatelliteFactory.create(test_name="Test Name")
        table_element = te.LinkTableElement(
            name="name",
            url="dummy_detail",
            kwargs={"pk": "pk"},
            icon="icon",
            hover_text="hover_text",
        )
        self.table_element_test_assertions_from_object(
            table_element=table_element,
            test_obj=test_obj,
            expected_format=f'<a id="id__baseclasses_{test_obj.id}_details" href="/baseclasses/{test_obj.id}/details"><span class="bi bi-icon"></span></a>',
            expected_format_latex=" \\color{black} \\twemoji{cross mark} &",
            expected_hover_text="hover_text",
        )

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

    def test_progress_bar__html(self):
        table_element = te.ProgressBarTableElement(
            name="name",
            attr="test_attr",
        )
        self.table_element_test_assertions_from_value(
            table_element=table_element,
            value=0.50,
            expected_format='<div class="bar-container"> <div class="bar" style="width: 50.0%;"></div> <span class="bar-value">50.00%</span> </div>',
            expected_format_latex="\\progressbar{ 50.0 }{ 50.00\\% } &",
            expected_td_classes=["text-end"],
            expected_style_attrs={"color": "#002F6C"},
        )

    def test_color_coded_table_element__html(self):
        color_codes = {
            "abc": ReportingColors.MEDIUM_BLUE,
            "def": ReportingColors.SOFT_ROSE,
        }
        table_element = te.ColorCodedStringTableElement(
            name="name", attr="test_attr", color_codes=color_codes
        )
        self.table_element_test_assertions_from_value(
            table_element=table_element,
            value="abc",
            expected_format="abc",
            expected_format_latex=" \\color{mediumblue} abc &",
            expected_td_classes=["text-start"],
            expected_style_attrs={"color": "#2B6D8B"},
        )
        self.table_element_test_assertions_from_value(
            table_element=table_element,
            value="def",
            expected_format="def",
            expected_format_latex=" \\color{softrose} def &",
            expected_td_classes=["text-start"],
            expected_style_attrs={"color": "#D3A9A1"},
        )
        self.table_element_test_assertions_from_value(
            table_element=table_element,
            value="ghi",
            expected_format="ghi",
            expected_format_latex=" \\color{blue} ghi &",
            expected_td_classes=["text-start"],
            expected_style_attrs={"color": "#004767"},
        )

    def test_label_table_element__html(self):
        color_codes = {
            "abc": ReportingColors.MEDIUM_BLUE,
            "def": ReportingColors.SOFT_ROSE,
        }
        table_element = te.LabelTableElement(
            name="name", attr="test_attr", color_codes=color_codes
        )
        self.table_element_test_assertions_from_value(
            table_element=table_element,
            value="abc",
            expected_format='<span class="badge" style="background-color:#2B6D8B;color:#FFFFFF;">abc</span>',
            expected_format_latex="\\colorbox[rgb]{0.169,0.427,0.545}{\\textcolor[HTML]{FFFFFF}{\\textbf{abc}}} &",
            expected_td_classes=["text-center"],
        )
        self.table_element_test_assertions_from_value(
            table_element=table_element,
            value="def",
            expected_format='<span class="badge" style="background-color:#D3A9A1;color:#000000;">def</span>',
            expected_format_latex="\\colorbox[rgb]{0.827,0.663,0.631}{\\textcolor[HTML]{000000}{\\textbf{def}}} &",
            expected_td_classes=["text-center"],
        )
        self.table_element_test_assertions_from_value(
            table_element=table_element,
            value="ghi",
            expected_format='<span class="badge" style="background-color:#004767;color:#FFFFFF;">ghi</span>',
            expected_format_latex="\\colorbox[rgb]{0.000,0.278,0.404}{\\textcolor[HTML]{FFFFFF}{\\textbf{ghi}}} &",
            expected_td_classes=["text-center"],
        )


@dataclass
class MockObject:
    name: str
    nested: dict


class TestGetDottedAttrOrArgTests(TestCase):
    def test_get_dotted_attr_or_arg_dict(self):
        mixin = te.GetDottetAttrsOrArgMixin
        obj = {"level1": {"level2": "value"}}
        result = mixin.get_dotted_attr_or_arg(obj, "level1.level2")
        self.assertEqual("value", result)

    def test_get_dotted_attr_or_arg_missing(self):
        mixin = te.GetDottetAttrsOrArgMixin
        obj = {"level1": {}}
        result = mixin.get_dotted_attr_or_arg(obj, "level1.missing")
        self.assertIsNone(result)

    def test_get_dotted_attr_or_arg_obj(self):
        mixin = te.GetDottetAttrsOrArgMixin
        obj = MockObject(name="Test Name", nested={"value": "Nested Value"})
        result = mixin.get_dotted_attr_or_arg(obj, "nested.value")
        self.assertEqual("Nested Value", result)
