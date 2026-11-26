from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.tests.factories import montrek_example_factories as me_factories
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from reporting.tests.managers.test_summary_row import DoubledIntTableElement, cells


class HubCSummaryTableManager(MontrekTableManager):
    repository_class = HubCRepository
    show_summary_row = True

    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_tsc3_str"),
            te.IntTableElement(name="Count", attr="field_tsc3_int"),
            te.PercentTableElement(name="Share", attr="field_tsc3_int"),
        )


class HubCComputedSummaryTableManager(HubCSummaryTableManager):
    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_tsc3_str"),
            DoubledIntTableElement(name="Doubled", attr="field_tsc3_int"),
        )


class HubCSameFieldSummaryTableManager(HubCSummaryTableManager):
    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_tsc3_str"),
            te.IntTableElement(name="Count", attr="field_tsc3_int"),
            DoubledIntTableElement(name="Doubled", attr="field_tsc3_int"),
        )


class HubCFloatColumnSummaryTableManager(HubCSummaryTableManager):
    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_tsc3_str"),
            te.IntTableElement(name="Whole", attr="field_tsc2_float"),
            te.FloatTableElement(name="Exact", attr="field_tsc2_float"),
        )


class HubASummaryTableManager(MontrekTableManager):
    repository_class = HubARepository
    show_summary_row = True

    @property
    def table_elements(self):
        return (
            te.StringTableElement(name="Name", attr="field_a1_str"),
            te.IntTableElement(name="Count", attr="field_a1_int"),
            te.FloatTableElement(name="Amount", attr="field_a2_float"),
        )


class TestSummaryRowOfQuerysets(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        for name, count in (("a", 1), ("b", 2), ("c", 4)):
            me_factories.SatTSC3Factory(field_tsc3_str=name, field_tsc3_int=count)
        me_factories.SatTSC3Factory(field_tsc3_str="empty", field_tsc3_int=None)

    def test_sums_in_one_query(self):
        manager = HubCSummaryTableManager({"user_id": self.user.id})
        with CaptureQueriesContext(connection) as queries:
            fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual(
            cells(fields),
            [
                ("Name", "Sum", None),
                ("Count", "7", 7),
                # Shares are not added up
                ("Share", "", None),
            ],
        )
        self.assertEqual(len(queries), 1)
        self.assertIn("SUM(", queries[0]["sql"])

    def test_sums_computed_values_in_python(self):
        manager = HubCComputedSummaryTableManager({"user_id": self.user.id})
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual(fields[1].value, 14)

    def test_columns_of_the_same_field_in_sql_and_python(self):
        manager = HubCSameFieldSummaryTableManager({"user_id": self.user.id})
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual([field.value for field in fields[1:]], [7, 14])

    def test_integers_of_a_float_column_sum_as_shown(self):
        for _ in range(2):
            me_factories.SatTSC2Factory(field_tsc2_float=1.8)
        manager = HubCFloatColumnSummaryTableManager({"user_id": self.user.id})
        fields = manager.get_summary_fields(manager.table_elements)

        # Each row shows 1, so the column sums to 2, not to int(3.6)
        self.assertEqual(fields[1].value, 2)
        self.assertAlmostEqual(fields[2].value, 3.6)

    def test_repository_sums_only_numeric_columns(self):
        queryset = HubCRepository({}).receive()

        self.assertEqual(
            HubCRepository.get_column_sums(
                queryset, ["field_tsc3_int", "field_tsc3_str", "no_such_field"]
            ),
            {"field_tsc3_int": 7},
        )


class TestSummaryRowOfViewModels(TestCase):
    def test_sums_the_columns_of_the_view_model(self):
        user = MontrekUserFactory()
        repository = HubARepository({"user_id": user.id})
        for name, count, amount in (("a", 1, 1.5), ("b", 2, 2.5)):
            repository.create_by_dict(
                {
                    "field_a1_str": name,
                    "field_a1_int": count,
                    "field_a2_str": name,
                    "field_a2_float": amount,
                }
            )
        manager = HubASummaryTableManager({"user_id": user.id})
        fields = manager.get_summary_fields(manager.table_elements)

        self.assertEqual([field.value for field in fields[1:]], [3, 4.0])
