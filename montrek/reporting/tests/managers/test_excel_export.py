import datetime
import io
from decimal import Decimal

import pandas as pd
from django.test import TestCase
from openpyxl import load_workbook

from reporting.managers.excel_export import ExcelSheetMixin
from reporting.tests.mocks import MockMontrekDataFrameTableManager


class TestDecimalsAsFloats(TestCase):
    def test_decimals_become_floats(self):
        frame = pd.DataFrame({"amount": [Decimal("1.25"), None], "name": ["a", "b"]})

        converted = ExcelSheetMixin.decimals_as_floats(frame)

        self.assertEqual(converted["amount"].tolist()[0], 1.25)
        self.assertIsInstance(converted["amount"].tolist()[0], float)
        self.assertEqual(converted["name"].tolist(), ["a", "b"])

    def test_columns_sharing_a_header(self):
        frame = pd.DataFrame([[Decimal("1"), Decimal("2")]], columns=["x", "x"])

        converted = ExcelSheetMixin.decimals_as_floats(frame)

        self.assertEqual(converted.iloc[0].tolist(), [1.0, 2.0])

    def test_leaves_the_frame_alone(self):
        frame = pd.DataFrame({"amount": [Decimal("1")]})

        ExcelSheetMixin.decimals_as_floats(frame)

        self.assertIsInstance(frame["amount"].iloc[0], Decimal)


class TestDataFrameTableExcel(TestCase):
    def test_decimals_are_written_as_numbers(self):
        df = pd.DataFrame(
            {
                "field_a": ["a", "b"],
                "field_b": [1, 2],
                "field_c": [1.5, 2.5],
                "field_d": [datetime.date(2024, 7, 13), datetime.date(2024, 7, 14)],
                "field_e": [Decimal("1000.25"), Decimal("NaN")],
                "Link Text": ["a", "b"],
            }
        )
        manager = MockMontrekDataFrameTableManager(
            {"df_data": df.to_dict(orient="records")}
        )

        sheet = load_workbook(manager.to_excel(io.BytesIO())).active

        header = [cell.value for cell in sheet[1]]
        amount = sheet.cell(row=2, column=header.index("Field E") + 1)
        self.assertEqual(amount.value, 1000.25)
        self.assertEqual(amount.data_type, "n")
        missing = sheet.cell(row=3, column=header.index("Field E") + 1)
        self.assertIsNone(missing.value)
        self.assertEqual(sheet.cell(row=2, column=1).value, "a")

    def test_number_formats_follow_the_headers(self):
        df = pd.DataFrame(
            {
                # Not a column of the table, but in the sheet
                "key": ["k1", "k2"],
                "field_a": ["a", "b"],
                "field_b": [1, 2],
                "field_c": [1.5, 2.5],
                "field_d": [datetime.date(2024, 7, 13), datetime.date(2024, 7, 14)],
                "field_e": [Decimal("1000.25"), Decimal("2")],
                "Link Text": ["a", "b"],
            }
        )
        manager = MockMontrekDataFrameTableManager(
            {"df_data": df.to_dict(orient="records")}
        )

        sheet = load_workbook(manager.to_excel(io.BytesIO())).active

        header = [cell.value for cell in sheet[1]]
        formats = {
            name: sheet.cell(row=2, column=index + 1).number_format
            for index, name in enumerate(header)
        }
        self.assertEqual(formats["key"], "General")
        self.assertEqual(formats["Field B"], "#,##0")
        self.assertEqual(formats["Field C"], "#,##0.000")
        self.assertEqual(formats["Field E"], "#,##0.00")
