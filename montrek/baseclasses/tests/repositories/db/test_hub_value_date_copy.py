import datetime
from io import StringIO
from typing import cast

from django.core.management import CommandError, call_command
from django.test import TestCase

from baseclasses.models import TestHubValueDate
from baseclasses.repositories.db.hub_value_date_copy import HubValueDateCopy
from baseclasses.tests.factories.baseclass_factories import (
    TestHubValueDateFactory,
    TestMontrekHubFactory,
)
from baseclasses.tests.factories.montrek_factory_schemas import ValueDateListFactory
from info.models.test_models import TestHubValueDateA
from montrek_example.models import example_models as me_models
from montrek_example.repositories.hub_c_repository import HubCRepository
from user.tests.factories.montrek_user_factories import MontrekUserFactory

DATE = datetime.date(2024, 1, 15)


def dated_row(hub, value_date=DATE) -> TestHubValueDate:
    return cast(
        TestHubValueDate,
        TestHubValueDateFactory(
            hub=hub, value_date_list=ValueDateListFactory(value_date=value_date)
        ),
    )


class TestValueDateCopyIsWritten(TestCase):
    def test_save_copies_the_date(self):
        row = dated_row(TestMontrekHubFactory())

        row.refresh_from_db()
        self.assertEqual(row.value_date_copy, DATE)

    def test_saving_a_new_value_date_row_updates_the_copy(self):
        row = dated_row(TestMontrekHubFactory())
        later = DATE + datetime.timedelta(days=1)
        row.value_date_list = ValueDateListFactory(value_date=later)

        row.save(update_fields=["value_date_list"])

        row.refresh_from_db()
        self.assertEqual(row.value_date_copy, later)

    def test_undated_row_has_no_copy(self):
        hub = TestMontrekHubFactory()

        self.assertEqual(
            list(
                TestHubValueDate.objects.filter(hub=hub).values_list(
                    "value_date_copy", flat=True
                )
            ),
            [None],
        )

    def test_create_by_dict_copies_the_date(self):
        user = MontrekUserFactory()
        hub = HubCRepository({"user_id": user.pk}).create_by_dict(
            {"field_tsc2_float": 0.1, "value_date": DATE}
        )

        self.assertEqual(
            list(
                me_models.CHubValueDate.objects.filter(
                    hub=hub, value_date_list__value_date=DATE
                ).values_list("value_date_copy", flat=True)
            ),
            [DATE],
        )


class TestFill(TestCase):
    def test_fills_dated_rows_without_copy(self):
        row = dated_row(TestMontrekHubFactory())
        TestHubValueDate.objects.filter(pk=row.pk).update(value_date_copy=None)

        filled = HubValueDateCopy(["baseclasses"]).fill()

        row.refresh_from_db()
        self.assertEqual(row.value_date_copy, DATE)
        self.assertEqual(filled[TestHubValueDate], 1)

    def test_leaves_undated_rows_alone(self):
        TestMontrekHubFactory()

        filled = HubValueDateCopy(["baseclasses"]).fill()

        self.assertEqual(filled[TestHubValueDate], 0)


class TestCheck(TestCase):
    def _finding(self):
        (finding,) = (
            finding
            for finding in HubValueDateCopy(["baseclasses"]).check()
            if finding.model is TestHubValueDate
        )
        return finding

    def test_consistent_rows(self):
        hub = TestMontrekHubFactory()
        dated_row(hub)
        dated_row(hub, DATE + datetime.timedelta(days=1))

        self.assertTrue(self._finding().is_consistent)

    def test_stale_copy(self):
        hub = TestMontrekHubFactory()
        older = dated_row(hub)
        dated_row(hub, DATE + datetime.timedelta(days=1))
        TestHubValueDate.objects.filter(pk=older.pk).update(
            value_date_copy=DATE + datetime.timedelta(days=5)
        )

        finding = self._finding()

        self.assertEqual(finding.stale_copies, 1)
        self.assertFalse(finding.is_consistent)

    def test_missing_copy_is_stale(self):
        row = dated_row(TestMontrekHubFactory())
        TestHubValueDate.objects.filter(pk=row.pk).update(value_date_copy=None)

        self.assertEqual(self._finding().stale_copies, 1)


class TestModels(TestCase):
    def test_leaves_out_unmanaged_models(self):
        self.assertNotIn(TestHubValueDateA, HubValueDateCopy(["info"]).models)


class TestCheckHubValueDatesCommand(TestCase):
    def test_succeeds_when_consistent(self):
        dated_row(TestMontrekHubFactory())
        out = StringIO()

        call_command("check_hub_value_dates", "baseclasses", stdout=out)

        self.assertIn("consistent", out.getvalue())

    def test_fails_on_a_stale_copy(self):
        row = dated_row(TestMontrekHubFactory())
        TestHubValueDate.objects.filter(pk=row.pk).update(value_date_copy=None)
        out = StringIO()

        with self.assertRaises(CommandError):
            call_command("check_hub_value_dates", "baseclasses", stdout=out)
        self.assertIn("baseclasses.TestHubValueDate: 1 stale copies", out.getvalue())

    def test_unknown_app_label(self):
        with self.assertRaises(CommandError):
            call_command("check_hub_value_dates", "no_such_app")
