import datetime
from django.test import TestCase

from reporting.managers.montrek_table_manager import MontrekTableManager


class TestReportingRegression(TestCase):
    def test_handle_date_naive(self):
        montrek_table = MontrekTableManager()
        test_date = datetime.date(2024, 8, 15)
        # Test that no error is raised
        montrek_table._make_datetime_naive(test_date)
