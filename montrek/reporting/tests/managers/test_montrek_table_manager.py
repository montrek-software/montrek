import datetime
from decimal import Decimal
import io

import pandas as pd
from bs4 import BeautifulSoup
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from user.tests.factories.montrek_user_factories import MontrekUserFactory
from reporting.tests.mocks import (
    MockMontrekTableManager,
    MockLongMontrekTableManager,
    MockMontrekDataFrameTableManager,
)


class TestMontrekTableManager(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()

    def test_to_html(self):
        test_html = MockMontrekTableManager().to_html()
        soup = BeautifulSoup(test_html, "html.parser")
        table = soup.find("table")
        rows = table.find_all("tr")
        self.assertEqual(len(rows), 4)
        headers = soup.find_all("th")
        expected_headers = [
            "Field A",
            "Field B",
            "Field C",
            "Field D",
            "Field E",
            "Link",
            "Link Text",
        ]
        header_texts = [th.get_text() for th in headers]
        self.assertEqual(header_texts, expected_headers)

    def test_to_latex(self):
        test_latex = MockMontrekTableManager().to_latex()
        self.assertTrue(test_latex.startswith("\n\\begin{table}"))
        self.assertTrue(test_latex.endswith("\\end{table}\n\n"))

    def test_download_csv(self):
        manager = MockMontrekTableManager()
        response = manager.download_or_mail_csv()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "text/csv",
        )
        # Check the Content-Disposition header using regex
        content_disposition = response["Content-Disposition"]
        filename_pattern = r'attachment; filename="mockmontrektablemanager_\d{14}\.csv"'
        self.assertRegex(content_disposition, filename_pattern)
        self.assertEqual(
            response.getvalue(),
            b"Field A,Field B,Field C,Field D,Field E,Link Text\na,1,1.0,2024-07-13,1.0,a\nb,2,2.0,2024-07-13,2.2,b\nc,3,3.0,2024-07-13,3.0,c\n",
        )

    def test_download_excel(self):
        manager = MockMontrekTableManager()
        response = manager.download_or_mail_excel()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        # Check the Content-Disposition header using regex
        content_disposition = response["Content-Disposition"]
        filename_pattern = (
            r'attachment; filename="mockmontrektablemanager_\d{14}\.xlsx"'
        )
        self.assertRegex(content_disposition, filename_pattern)
        with io.BytesIO(response.content) as f:
            excel_file = pd.read_excel(f)
            expected_df = pd.DataFrame(
                {
                    "Field A": ["a", "b", "c"],
                    "Field B": [1, 2, 3],
                    "Field C": [1.0, 2.0, 3.0],
                    "Field D": [
                        datetime.datetime(2024, 7, 13),
                        datetime.datetime(2024, 7, 13),
                        timezone.datetime(2024, 7, 13),
                    ],
                    "Field E": [1, 2.2, 3],
                    "Link Text": ["a", "b", "c"],
                }
            )
            pd.testing.assert_frame_equal(excel_file, expected_df, check_dtype=False)

    def test_get_table_elements_name_to_field_map(self):
        manager = MockMontrekTableManager()
        name_to_field_map = manager.get_table_elements_name_to_field_map()
        expected_map = {
            "Field A": "field_a",
            "Field B": "field_b",
            "Field C": "field_c",
            "Field D": "field_d",
            "Field E": "field_e",
            "Link": "",
            "Link Text": "",
        }
        self.assertEqual(name_to_field_map, expected_map)

    def test_large_download_excel(self):
        manager = MockLongMontrekTableManager(
            {"user_id": self.user.id, "host_url": "test_server"}
        )
        response = manager.download_or_mail_excel()
        self.assertEqual(response.status_code, 302)
        sent_email = mail.outbox[0]
        self.assertTrue(sent_email.subject.endswith(".xlsx is ready for download"))
        self.assertEqual(sent_email.to, [self.user.email])
        self.assertTrue(
            "Please download the table from the link below:"
            in sent_email.message().as_string()
        )
        self.assertEqual(
            manager.messages[-1].message,
            "Table is too large to download. Sending it by mail.",
        )

    def test_large_download_csv(self):
        manager = MockLongMontrekTableManager(
            {"user_id": self.user.id, "host_url": "test_server"}
        )
        response = manager.download_or_mail_csv()
        self.assertEqual(response.status_code, 302)
        sent_email = mail.outbox[0]
        self.assertTrue(sent_email.subject.endswith(".csv is ready for download"))
        self.assertEqual(sent_email.to, [self.user.email])
        self.assertTrue(
            "Please download the table from the link below:"
            in sent_email.message().as_string()
        )
        self.assertEqual(
            manager.messages[-1].message,
            "Table is too large to download. Sending it by mail.",
        )

    def test_set_paginate_by(self):
        test_manager = MockLongMontrekTableManager({})
        self.assertEqual(test_manager.paginate_by, 10)
        query = test_manager.get_table()
        self.assertEqual(len(query), 10)

        test_manager = MockLongMontrekTableManager({"current_paginate_by": 20})
        self.assertEqual(test_manager.paginate_by, 20)
        query = test_manager.get_table()
        self.assertEqual(len(query), 20)
        test_manager = MockLongMontrekTableManager({"current_paginate_by": 0})
        self.assertEqual(test_manager.paginate_by, 5)
        query = test_manager.get_table()
        self.assertEqual(len(query), 5)

    def test_set_is_compact_format(self):
        test_manager = MockLongMontrekTableManager({})
        self.assertEqual(test_manager.is_current_compact_format, False)

        test_manager = MockLongMontrekTableManager({"current_is_compact_format": True})
        self.assertEqual(test_manager.is_current_compact_format, True)
        test_manager = MockLongMontrekTableManager({"current_is_compact_format": False})
        self.assertEqual(test_manager.is_current_compact_format, False)

    def test_order_field(self):
        test_manager = MockLongMontrekTableManager({})
        self.assertEqual(test_manager.order_field, None)
        self.assertEqual(test_manager.repository.get_order_fields(), None)

        test_manager = MockLongMontrekTableManager({"order_field": "field_a"})
        self.assertEqual(test_manager.order_field, "field_a")
        self.assertEqual(test_manager.repository.get_order_fields(), "field_a")
        test_manager = MockLongMontrekTableManager({"order_field": "-field_a"})
        self.assertEqual(test_manager.order_field, "-field_a")
        self.assertEqual(test_manager.repository.get_order_fields(), "-field_a")


class TestMontrekDataFrameTableManager(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        input_df = pd.DataFrame(
            {
                "field_a": ["a", "b", "c"],
                "field_b": [1, 2, 3],
                "field_c": [1.0, 2.0, 3.0],
                "field_d": [
                    datetime.datetime(2024, 7, 13),
                    datetime.datetime(2024, 7, 13),
                    timezone.datetime(2024, 7, 13),
                ],
                "field_e": [Decimal(1), Decimal(2), Decimal(3)],
                "Link Text": ["a", "b", "c"],
            }
        )
        large_df = pd.DataFrame(
            {
                "field_a": ["a", "b", "c"] * 10000,
                "field_b": [1, 2, 3] * 10000,
                "field_c": [1.0, 2.0, 3.0] * 10000,
                "field_d": [
                    datetime.datetime(2024, 7, 13),
                    datetime.datetime(2024, 7, 13),
                    timezone.datetime(2024, 7, 13),
                ]
                * 10000,
                "Link Text": ["a", "b", "c"] * 10000,
            }
        )
        self.manager = MockMontrekDataFrameTableManager(
            {
                "user_id": self.user.id,
                "host_url": "test_server",
                "df_data": input_df.to_dict(orient="records"),
            }
        )
        self.large_manager = MockMontrekDataFrameTableManager(
            {
                "user_id": self.user.id,
                "host_url": "test_server",
                "df_data": large_df.to_dict(orient="records"),
            }
        )

    def test_to_html(self):
        test_html = self.manager.to_html()
        soup = BeautifulSoup(test_html, "html.parser")
        table = soup.find("table")
        rows = table.find_all("tr")
        self.assertEqual(len(rows), 4)
        headers = soup.find_all("th")
        expected_headers = [
            "Field A",
            "Field B",
            "Field C",
            "Field D",
            "Field E",
            "Link",
            "Link Text",
        ]
        header_texts = [th.get_text() for th in headers]
        self.assertEqual(header_texts, expected_headers)

    def test_to_latex(self):
        test_latex = self.manager.to_latex()
        self.assertTrue(test_latex.startswith("\n\\begin{table}"))
        self.assertTrue(test_latex.endswith("\\end{table}\n\n"))

    def test_download_csv(self):
        response = self.manager.download_or_mail_csv()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "text/csv",
        )
        # Check the Content-Disposition header using regex
        content_disposition = response["Content-Disposition"]
        filename_pattern = (
            r'attachment; filename="mockmontrekdataframetablemanager_\d{14}\.csv"'
        )
        self.assertRegex(content_disposition, filename_pattern)
        self.assertEqual(
            response.getvalue(),
            b"Field A,Field B,Field C,Field D,Field E,Link Text\na,1,1.0,2024-07-13,1,a\nb,2,2.0,2024-07-13,2,b\nc,3,3.0,2024-07-13,3,c\n",
        )

    def test_download_excel(self):
        response = self.manager.download_or_mail_excel()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        # Check the Content-Disposition header using regex
        content_disposition = response["Content-Disposition"]
        filename_pattern = (
            r'attachment; filename="mockmontrekdataframetablemanager_\d{14}\.xlsx"'
        )
        self.assertRegex(content_disposition, filename_pattern)
        with io.BytesIO(response.content) as f:
            excel_file = pd.read_excel(f)
            expected_df = pd.DataFrame(
                {
                    "Field A": ["a", "b", "c"],
                    "Field B": [1, 2, 3],
                    "Field C": [1.0, 2.0, 3.0],
                    "Field D": [
                        datetime.datetime(2024, 7, 13),
                        datetime.datetime(2024, 7, 13),
                        timezone.datetime(2024, 7, 13),
                    ],
                    "Field E": [1.0, 2.0, 3.0],
                    "Link Text": ["a", "b", "c"],
                }
            )
            pd.testing.assert_frame_equal(excel_file, expected_df, check_dtype=False)

    def test_get_table_elements_name_to_field_map(self):
        name_to_field_map = self.manager.get_table_elements_name_to_field_map()
        expected_map = {
            "Field A": "field_a",
            "Field B": "field_b",
            "Field C": "field_c",
            "Field D": "field_d",
            "Field E": "field_e",
            "Link": "",
            "Link Text": "",
        }
        self.assertEqual(name_to_field_map, expected_map)

    def test_large_download_excel(self):
        response = self.large_manager.download_or_mail_excel()
        self.assertEqual(response.status_code, 302)
        sent_email = mail.outbox[0]
        self.assertTrue(sent_email.subject.endswith(".xlsx is ready for download"))
        self.assertEqual(sent_email.to, [self.user.email])
        self.assertTrue(
            "Please download the table from the link below:"
            in sent_email.message().as_string()
        )
        self.assertEqual(
            self.large_manager.messages[-1].message,
            "Table is too large to download. Sending it by mail.",
        )

    def test_large_download_csv(self):
        response = self.large_manager.download_or_mail_csv()

        self.assertEqual(response.status_code, 302)
        sent_email = mail.outbox[0]
        self.assertTrue(sent_email.subject.endswith(".csv is ready for download"))
        self.assertEqual(sent_email.to, [self.user.email])
        self.assertTrue(
            "Please download the table from the link below:"
            in sent_email.message().as_string()
        )
        self.assertEqual(
            self.large_manager.messages[-1].message,
            "Table is too large to download. Sending it by mail.",
        )
