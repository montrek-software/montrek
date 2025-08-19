import warnings

from baseclasses import models as bc_models
from baseclasses.repositories.subquery_builder import (
    GroupConcat,
    LinkedSatelliteSubqueryBuilder,
    StringAgg,
    SubqueryBuilder,
    get_string_concat_function,
)
from baseclasses.tests.factories.baseclass_factories import (
    LinkTestMontrekTestLinkFactory,
    TestLinkSatelliteFactory,
)
from baseclasses.utils import montrek_time
from django.db.models import CharField
from django.test import TestCase
from django.utils import timezone

warnings.filterwarnings(
    "ignore",
    message="Overriding setting DATABASES can lead to unexpected behavior.",
    category=UserWarning,
)


class MockLinkedSatelliteSubqueryBuilder(LinkedSatelliteSubqueryBuilder):
    field_type = CharField()

    def _is_multiple_allowed(self, hub_field_to: str) -> bool:
        return True


class TestLinkedSatelliteSubqueryBuilder(TestCase):
    def setUp(self):
        self.reference_date = montrek_time(2023, 6, 25)
        link_entry_1 = LinkTestMontrekTestLinkFactory()
        link_entry_2_1 = LinkTestMontrekTestLinkFactory(
            state_date_end=self.reference_date
        )
        link_entry_2_2 = LinkTestMontrekTestLinkFactory(
            hub_in=link_entry_2_1.hub_in, state_date_start=self.reference_date
        )
        self.sat_1 = TestLinkSatelliteFactory(
            hub_entity=link_entry_1.hub_out,
        )
        self.sat_2_1 = TestLinkSatelliteFactory(
            hub_entity=link_entry_2_1.hub_out,
        )
        self.sat_2_2 = TestLinkSatelliteFactory(
            hub_entity=link_entry_2_2.hub_out,
        )

    def test_build_not_impolemented(self):
        with self.assertRaises(NotImplementedError) as cm:
            SubqueryBuilder().build(reference_date=timezone.now())
        self.assertEqual(
            str(cm.exception),
            "SubqueryBuilder must be subclassed and the build method must be implemented!",
        )

    def test_get_subquery(self):
        builder = LinkedSatelliteSubqueryBuilder(
            satellite_class=bc_models.TestLinkSatellite,
            field="test_id",
            link_class=bc_models.LinkTestMontrekTestLink,
        )
        subquery = builder.build(self.reference_date)
        query = bc_models.TestHubValueDate.objects.annotate(**{"test_id": subquery})
        self.assertEqual(len(query), 2)
        self.assertEqual(query[0].test_id, self.sat_1.test_id)
        self.assertEqual(query[1].test_id, self.sat_2_2.test_id)

        builder = LinkedSatelliteSubqueryBuilder(
            satellite_class=bc_models.TestLinkSatellite,
            field="test_id",
            link_class=bc_models.LinkTestMontrekTestLink,
        )
        subquery = builder.build(self.reference_date + timezone.timedelta(days=1))
        query = bc_models.TestHubValueDate.objects.annotate(**{"test_id": subquery})
        self.assertEqual(len(query), 2)
        self.assertEqual(query[0].test_id, self.sat_1.test_id)
        self.assertEqual(query[1].test_id, self.sat_2_2.test_id)

        subquery = builder.build(self.reference_date + timezone.timedelta(days=-1))
        query = bc_models.TestHubValueDate.objects.annotate(**{"test_id": subquery})
        self.assertEqual(len(query), 2)
        self.assertEqual(query[0].test_id, self.sat_1.test_id)
        # self.assertEqual(query[1].test_id, self.sat_2_1.test_id)
        #

    def test_no_agg_func(self):
        builder = MockLinkedSatelliteSubqueryBuilder(
            satellite_class=bc_models.TestLinkSatellite,
            field="test_id",
            link_class=bc_models.LinkTestMontrekTestLink,
        )
        builder.agg_func = None
        self.assertRaises(NotImplementedError, builder._annotate_agg_field, "", [])

    def test_raise_error_when_no_relation_to_link_table_is_set(self):
        class DummyLinkClass(bc_models.MontrekLinkABC):
            class Meta:
                managed = False
                abstract = True

        with self.assertRaisesMessage(
            TypeError, "DummyLinkClass must inherit from valid LinkClass!"
        ):
            LinkedSatelliteSubqueryBuilder(
                bc_models.TestLinkSatellite,
                "test_id",
                DummyLinkClass,
            )


class TestSideFunctions(TestCase):
    def test_get_string_concat_function(self):
        with self.settings(DATABASES={"default": {"ENGINE": "mysql"}}):
            act = get_string_concat_function(separator="|")()
            exp = GroupConcat(separator="|")
            self.assertEqual(act, exp)
            self.assertEqual(
                act.template, "GROUP_CONCAT(%(expressions)s SEPARATOR '|')"
            )
        with self.settings(DATABASES={"default": {"ENGINE": "postgresql"}}):
            act = get_string_concat_function(separator=",")()
            exp = StringAgg(separator=",")
            self.assertEqual(act, exp)
            self.assertEqual(act.template, "STRING_AGG(%(expressions)s, ',')")
        with self.settings(DATABASES={"default": {"ENGINE": "unknown"}}):
            self.assertRaises(
                NotImplementedError, get_string_concat_function, separator=","
            )
