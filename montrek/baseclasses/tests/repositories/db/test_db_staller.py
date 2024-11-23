from django.test import TestCase
from baseclasses.repositories.db.db_staller import DbStaller

from baseclasses.models import TestMontrekHub, TestMontrekSatellite


class TestDbStallerNewSatellite(TestCase):
    def test_db_staller__add_and_get_new_satellites(self):
        new_sat = TestMontrekSatellite()
        db_staller = DbStaller()
        db_staller.stall_new_satellite(new_sat)
        db_staller_new_sats = db_staller.get_new_satellites()[new_sat.__class__]
        self.assertEqual(len(db_staller_new_sats), 1)
        self.assertEqual(db_staller_new_sats[0], new_sat)

    def test_db_staller__add_and_get_new_satellites__multiple_satellites(self):
        new_sat1 = TestMontrekSatellite()
        new_sat2 = TestMontrekSatellite()
        db_staller = DbStaller()
        db_staller.stall_new_satellite(new_sat1)
        db_staller.stall_new_satellite(new_sat2)
        db_staller_new_sats = db_staller.get_new_satellites()[new_sat1.__class__]
        self.assertEqual(len(db_staller_new_sats), 2)
        self.assertEqual(db_staller_new_sats[0], new_sat1)
        self.assertEqual(db_staller_new_sats[1], new_sat2)


class TestDbStallerNewHub(TestCase):
    def test_db_staller__add_and_get_new_hub(self):
        new_hub = TestMontrekHub()
        db_staller = DbStaller()
        db_staller.stall_hub(new_hub)
        db_staller_new_hubs = db_staller.get_hubs()
        self.assertEqual(len(db_staller_new_hubs), 1)
        self.assertEqual(db_staller_new_hubs[0], new_hub)
