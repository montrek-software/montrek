import unittest.mock as mock

from django.test import TestCase

from baseclasses.repositories.db.db_data_frame import DbDataFrame


class MockDbDataFrame(DbDataFrame):
    def __init__(self):
        ...

    def get_link_field_names(self) -> list[str]:
        return []

    def get_static_satellite_field_names(self) -> list[str]:
        return []


class TestDbDataFrame(TestCase):
    def setUp(self):
        self.db_data_frame = MockDbDataFrame()

    def test_dont_process_data_when_static_columns_empty(self):
        self.db_data_frame._process_static_data()
        with mock.patch(
            "baseclasses.repositories.db.db_data_frame.DbDataFrame._process_data"
        ) as mock_process_data:
            mock_process_data.assert_not_called()
