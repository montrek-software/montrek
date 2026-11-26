import pandas as pd
from baseclasses.utils import montrek_time
from bs4 import BeautifulSoup
from django.test import TestCase
from montrek_example.models.example_models import SatA1
from montrek_example.tests.factories import montrek_example_factories as me_factories
from reporting.dataclasses.table_elements import HistoryChangeState
from reporting.managers.montrek_table_manager import HistoryDataTableManager
from user.tests.factories.montrek_user_factories import MontrekUserFactory


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
            onclick = f"document.getElementById('form-order_by-action').value='{col}'"
            button = soup.find("button", attrs={"onclick": onclick})
            self.assertIsNotNone(button)
            self.assertIn("btn-order-field", button["class"])

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
