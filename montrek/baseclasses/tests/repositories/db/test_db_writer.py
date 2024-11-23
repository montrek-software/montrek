from django.test import TestCase
from baseclasses.repositories.db.db_staller import DbStaller
from baseclasses.repositories.db.db_writer import DbWriter

from baseclasses.models import TestMontrekSatellite, TestMontrekHub


class TestDbWriter(TestCase):
    def test_db_writer__add_and_write_new_satellite(self):
        new_hub = TestMontrekHub()
        new_sat = TestMontrekSatellite(hub_entity=new_hub)
        db_staller = DbStaller()
        db_staller.stall_new_satellite(new_sat)
        db_writer = DbWriter(db_staller)
        db_writer.write()
        new_sats = TestMontrekSatellite.objects.all()
        self.assertEqual(len(new_sats), 1)
        self.assertEqual(new_sats[0], new_sat)
