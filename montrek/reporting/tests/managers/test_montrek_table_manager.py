import datetime
import io
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
from baseclasses.utils import montrek_time
from bs4 import BeautifulSoup
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from montrek_example.models.example_models import SatA1
from montrek_example.tests.factories import montrek_example_factories as me_factories
from reporting.dataclasses.table_elements import HistoryChangeState
from reporting.managers.montrek_table_manager import HistoryDataTableManager
from reporting.tests.mocks import (
    MockHtmlMontrekTableManager,
    MockLongMontrekTableManager,
    MockLongMontrekTableManager2,
    MockMontrekDataFrameTableManager,
    MockMontrekTableManager,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestMontrekTableManager(TestCase):
    BASE_DIR = Path(__file__).resolve().parent.parent
    rebase = False

    def setUp(self):
        self.user = MontrekUserFactory()

    def normailze_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        return soup.prettify()

    def test_to_html_exact_match(self):
        html = MockMontrekTableManager().to_html()
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        normalized = self.normailze_html(str(table))
        if self.rebase:
            (self.BASE_DIR / "data" / "html_exact.html").write_text(
                normalized, encoding="utf-8"
            )
            return

        expected = (self.BASE_DIR / "data" / "html_exact.html").read_text(
            encoding="utf-8"
        )

        self.assertEqual(normalized, expected)

    def test_to_latex(self):
        test_latex = MockMontrekTableManager().to_latex()
        self.assertTrue(test_latex.startswith("\n\\begin{table}"))
        self.assertTrue(test_latex.endswith("\\end{table}\n\n"))

    def test_to_json(self):
        test_json = MockMontrekTableManager().to_json()
        expected_json = [
            {
                "field_a": "a",
                "field_b": 1,
                "field_c": 1.0,
                "field_d": "2024-07-13T00:00:00",
                "field_e": 1.0,
            },
            {
                "field_a": "b",
                "field_b": 2,
                "field_c": 2.0,
                "field_d": "2024-07-13T00:00:00",
                "field_e": 2.2,
            },
            {
                "field_a": "c",
                "field_b": 3,
                "field_c": 3.0,
                "field_d": "2024-07-13T00:00:00",
                "field_e": 3.0,
            },
        ]
        self.assertEqual(test_json, expected_json)

    def test_download_csv(self):
        manager = MockMontrekTableManager()
        response = manager.download_or_mail_csv()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "text/csv",
        )
        content_disposition = response["Content-Disposition"]
        # Check the Content-Disposition header using regex
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
        for manager_cls in (MockLongMontrekTableManager, MockLongMontrekTableManager2):
            manager = manager_cls({"user_id": self.user.id, "host_url": "test_server"})
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
        for manager_cls in (MockLongMontrekTableManager, MockLongMontrekTableManager2):
            manager = manager_cls({"user_id": self.user.id, "host_url": "test_server"})
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
        self.assertFalse(test_manager.order_descending)
        test_manager.get_table()
        self.assertEqual(test_manager.repository.get_order_fields(), ("field_a",))
        test_manager = MockLongMontrekTableManager({"order_field": "-field_a"})
        self.assertEqual(test_manager.order_field, "-field_a")
        self.assertTrue(test_manager.order_descending)
        test_manager.get_full_table()
        self.assertEqual(test_manager.repository.get_order_fields(), ("-field_a",))

    def test_df_without_html(self):
        manager = MockHtmlMontrekTableManager()
        test_df = manager.get_df()
        self.assertEqual(test_df.loc[0, "Field A"], " · &  <  < >  > and _ ")


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
            "Field_A",
            "Field B",
            "Field C",
            "Field D",
            "Field E",
            "Link",
            "Link Text",
        ]
        header_texts = [th.get_text(strip=True) for th in headers]
        self.assertEqual(header_texts, expected_headers)

    def test_to_latex(self):
        test_latex = self.manager.to_latex()
        self.assertTrue(test_latex.startswith("\n\\begin{table}"))
        self.assertTrue(test_latex.endswith("\\end{table}\n\n"))
        self.assertIn("Field\\_A", test_latex)

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
            b"Field_A,Field B,Field C,Field D,Field E,Link Text\na,1,1.0,2024-07-13,1,a\nb,2,2.0,2024-07-13,2,b\nc,3,3.0,2024-07-13,3,c\n",
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
                    "Field_A": ["a", "b", "c"],
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
            "Field_A": "field_a",
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

    def test_convert_nan_to_json(self):
        input_df = pd.DataFrame(
            {
                "field_b": ["a", "b", np.nan],
            }
        )
        manager = MockMontrekDataFrameTableManager(
            {
                "user_id": self.user.id,
                "host_url": "test_server",
                "df_data": input_df.to_dict(orient="records"),
            }
        )
        test_json = manager.to_json()
        test_output = [dd["field_b"] for dd in test_json]
        self.assertEqual(test_output[2], None)


class TestHistoryDataTable(TestCase):
    def test_history_html(self):
        user1 = MontrekUserFactory()
        user2 = MontrekUserFactory()
        sat = me_factories.SatA1Factory(
            field_a1_str="TestFeld",
            field_a1_int=5,
            state_date_end=montrek_time(2024, 2, 17),
            created_by=user1,
            comment="initial comment",
        )
        me_factories.SatA1Factory(
            hub_entity=sat.hub_entity,
            field_a1_str="TestFeld",
            field_a1_int=6,
            state_date_start=montrek_time(2024, 2, 17),
            created_by=user2,
            comment="change comment",
        )
        me_factories.SatA2Factory(
            hub_entity=sat.hub_entity,
            field_a2_str="ConstantTestFeld",
            field_a2_float=6.0,
            created_by=user2,
            comment="another comment",
        )
        history_manager = HistoryDataTableManager({}, "SatA1", SatA1.objects.all())
        self.assertEqual(history_manager.title, "SatA1")
        html = history_manager.to_html()
        soup = BeautifulSoup(html, "html.parser")
        for col in (
            "state_date_start",
            "state_date_end",
            "comment",
            "created_by",
            "field_a1_str",
            "field_a1_int",
        ):
            th = soup.find("th", title=col)
            self.assertIsNotNone(th)

            button = th.find("button", {"class": "btn-order-field"})
            self.assertIsNotNone(button)

            self.assertEqual(
                button["onclick"],
                f"document.getElementById('form-order_by-action').value='{col}'",
            )

            self.assertEqual(button.text.strip(), col)

    def test_get_change_map_from_df(self):
        input_df = pd.DataFrame({"id": [1, 2], "col_1": ["A", "A"], "col_2": [2, 3]})
        test_dict = HistoryDataTableManager.get_change_map_from_df(input_df)
        self.assertEqual(
            test_dict,
            {
                1: {"col_2": HistoryChangeState.OLD},
                2: {"col_2": HistoryChangeState.NEW},
            },
        )
