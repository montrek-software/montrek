import datetime
from django.test import TestCase
from baseclasses.repositories.db.db_creator import DbCreator


class MockDbStaller:
    creation_date = None


class TestDBCreator(TestCase):
    def test_make_timezone_aware(self):
        test_db_creator = DbCreator(MockDbStaller(), 1)
        test_datetime = datetime.datetime(2018, 1, 1, 0, 0, 0)
        test_db_creator._make_timezone_aware(test_datetime, "UTC")
        self.assertEqual(test_db_creator.data["UTC"].tzinfo.key, "UTC")
