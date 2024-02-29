import os

from django.conf import settings
from django.test import TestCase

from company.managers.rgs import RgsFileProcessor


class TestRgsFileProcessor(TestCase):
    def test_read_file(self):
        file_path = os.path.join(
            settings.BASE_DIR, "company", "tests", "data", "rgs_test.xlsx"
        )
        df = RgsFileProcessor().read_file(file_path)

        assert df.shape[0] == 41076
