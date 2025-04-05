import pandas as pd
from info.managers.info_versions_managers import InfoVersionsManager
from info.modules.git_info import GitInfo
from info.views.info_views import InfoVersionsView


class MockGitInfo(GitInfo):
    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame({"repository": ["A", "B", "C"]})

    def _check_is_git_repo(self) -> bool:
        return True


class MockInfoVersionsManager(InfoVersionsManager):
    git_info_class = MockGitInfo


class MockInfoVersionsView(InfoVersionsView):
    manager_class = MockInfoVersionsManager
