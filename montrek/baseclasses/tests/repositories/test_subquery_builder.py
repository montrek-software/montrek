from django.test import TestCase
from django.utils import timezone
from baseclasses.utils import montrek_time
from baseclasses.tests.factories.baseclass_factories import TestMontrekSatelliteFactory
from baseclasses.tests.factories.baseclass_factories import TestLinkSatelliteFactory
from baseclasses.tests.factories.baseclass_factories import (
    LinkTestMontrekTestLinkFactory,
)
from baseclasses.repositories.subquery_builder import LinkedSatelliteSubqueryBuilder
from baseclasses import models as bc_models


class TestLinkedSatelliteSubqueryBuilder(TestCase):
    def setUp(self):
        self.reference_date = montrek_time(2023, 6, 25)
        link_entry_1 = LinkTestMontrekTestLinkFactory()
        link_entry_2_1 = LinkTestMontrekTestLinkFactory(
            state_date_end=self.reference_date
        )
        link_entry_2_2 = LinkTestMontrekTestLinkFactory(
            in_hub=link_entry_2_1.in_hub, state_date_start=self.reference_date
        )
        self.sat_1 = TestLinkSatelliteFactory(
            hub_entity=link_entry_1.out_hub,
        )
        self.sat_2_1 = TestLinkSatelliteFactory(
            hub_entity=link_entry_2_1.out_hub,
        )
        self.sat_2_2 = TestLinkSatelliteFactory(
            hub_entity=link_entry_2_2.out_hub,
        )

    def test_get_subquery(self):
        builder = LinkedSatelliteSubqueryBuilder(
            satellite_class=bc_models.TestLinkSatellite,
            link_class=bc_models.LinkTestMontrekTestLink,
            reference_date=self.reference_date,
        )
        subquery = builder.get_subquery("test_id")
        query = bc_models.TestMontrekHub.objects.annotate(**{"test_id": subquery})
        self.assertEqual(len(query), 2)
        self.assertEqual(query[0].test_id, self.sat_1.test_id)
        self.assertEqual(query[1].test_id, self.sat_2_2.test_id)

        builder = LinkedSatelliteSubqueryBuilder(
            satellite_class=bc_models.TestLinkSatellite,
            link_class=bc_models.LinkTestMontrekTestLink,
            reference_date=self.reference_date + timezone.timedelta(days=1),
        )
        subquery = builder.get_subquery("test_id")
        query = bc_models.TestMontrekHub.objects.annotate(**{"test_id": subquery})
        self.assertEqual(len(query), 2)
        self.assertEqual(query[0].test_id, self.sat_1.test_id)
        self.assertEqual(query[1].test_id, self.sat_2_2.test_id)

        builder = LinkedSatelliteSubqueryBuilder(
            satellite_class=bc_models.TestLinkSatellite,
            link_class=bc_models.LinkTestMontrekTestLink,
            reference_date=self.reference_date + timezone.timedelta(days=-1),
        )
        subquery = builder.get_subquery("test_id")
        query = bc_models.TestMontrekHub.objects.annotate(**{"test_id": subquery})
        self.assertEqual(len(query), 2)
        self.assertEqual(query[0].test_id, self.sat_1.test_id)
        self.assertEqual(query[1].test_id, self.sat_2_1.test_id)
