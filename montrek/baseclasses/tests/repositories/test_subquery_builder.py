from django.test import TestCase
from django.utils import timezone
from baseclasses.utils import montrek_time
from baseclasses.tests.factories.baseclass_factories import TestMontrekSatelliteFactory
from baseclasses.tests.factories.baseclass_factories import TestLinkSatelliteFactory
from baseclasses.repositories.subquery_builder import LinkedSatelliteSubqueryBuilder

class TestLinkedSatelliteSubqueryBuilder(TestCase):
    def setUp(self):
        self.test_sat_1 = TestMontrekSatelliteFactory.create()
        self.test_sat_2 = TestMontrekSatelliteFactory.create(
            hub_entity=self.test_sat_1.hub_entity,
            state_date_start=self.test_sat_1.state_date_end,
            state_date_end=timezone.datetime.max,
            test_name="test_sat_2",
            test_value=2,
        )
        self.test_linkes_sat_1_1 = TestLinkSatelliteFactory.create()
        self.test_linkes_sat_1_2 = TestLinkSatelliteFactory.create(
            hub_entity=self.test_linkes_sat_1_1.hub_entity,
            state_date_start=self.test_linkes_sat_1_1.state_date_end,
            state_date_end=timezone.datetime.max,
        )
        self.test_linkes_sat_1_1.hub_entity.link_link_hub_test_montrek_hub.add(
            self.test_sat_1.hub_entity
        )
        self.test_linkes_sat_2 = TestLinkSatelliteFactory.create()
        self.test_linkes_sat_2.hub_entity.link_link_hub_test_montrek_hub.add(
            self.test_sat_1.hub_entity
        )
