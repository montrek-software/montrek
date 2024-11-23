from django.test import TestCase
from baseclasses.repositories.db.db_staller import DbStaller

from baseclasses.tests.factories.baseclass_factories import (
    TestMontrekSatelliteFactory,
)


class TestDbStaller(TestCase):
    def test_db_staller__add_and_get_new_satellites(self):
        new_sat = TestMontrekSatelliteFactory.create()
        db_staller = DbStaller()
        db_staller.stall_new_satellite(new_sat)
        db_staller_new_sats = db_staller.get_new_satellites()[new_sat.__class__]
        self.assertEqual(len(db_staller_new_sats), 1)
        self.assertEqual(db_staller_new_sats[0], new_sat)
