import pandas as pd
from django.test import TestCase
from info.managers.info_versions_managers import InfoVersionsManager
from info.modules.git_info import GitInfo


class MockGitInfo(GitInfo):
    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame({"repository": ["A", "B", "C"]})

    def _check_is_git_repo(self) -> bool:
        return True


class MockInfoVersionsManager(InfoVersionsManager):
    git_info_class = MockGitInfo


class TestInfoVersionsManager(TestCase):
    def test_git_versions(self):
        manager = MockInfoVersionsManager({})
        git_versions_manager = manager.get_git_versions()
        pd.testing.assert_frame_equal(
            git_versions_manager.df,
            pd.DataFrame({"repository": ["A", "B", "C", "A", "B", "C"]}),
        )
