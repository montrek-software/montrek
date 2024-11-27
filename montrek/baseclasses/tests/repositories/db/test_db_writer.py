from django.test import TestCase
from baseclasses.repositories.db.db_staller import DbStaller
from baseclasses.repositories.db.db_writer import DbWriter
from baseclasses.repositories.annotator import Annotator

from baseclasses.models import TestMontrekSatellite, TestMontrekHub


class MockAnnotator(Annotator):
    def __init__(self, hub_class):
        super().__init__(hub_class)
        self.annotated_satellite_classes = [TestMontrekSatellite]


class TestDbWriter(TestCase):
    def setUp(self):
        annotator = MockAnnotator(TestMontrekHub)
        self.db_staller = DbStaller(annotator)

    def test_db_writer__add_and_write_new_satellite(self):
        new_hub = TestMontrekHub()
        new_sat = TestMontrekSatellite(hub_entity=new_hub)
        self.db_staller.stall_hub(new_hub)
        self.db_staller.stall_new_satellite(new_sat)
        db_writer = DbWriter(self.db_staller)
        db_writer.write()
        new_sats = TestMontrekSatellite.objects.all()
        self.assertEqual(len(new_sats), 1)
        self.assertEqual(new_sats[0], new_sat)
