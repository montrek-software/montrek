import pandas as pd
from django.test import TestCase
from info.managers.info_versions_managers import InfoVersionsManager


class TestInfoVersionsManager(TestCase):
    def test_git_versions(self):
        manager = InfoVersionsManager({})
        git_versions_manager = manager.get_git_versions()
        pd.testing.assert_frame_equal(
            git_versions_manager.df, pd.DataFrame({"repository": ["A", "B", "C"]})
        )
