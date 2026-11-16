from pathlib import Path

import pandas as pd
from django.conf import settings

from baseclasses.typing import TableElementsType
from info.modules.git_info import GitInfo
from info.modules.release_info import ReleaseInfo
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.managers.montrek_table_manager import MontrekDataFrameTableManager


class GitVersionsManager(MontrekDataFrameTableManager):
    @property
    def table_elements(self) -> TableElementsType:
        return (
            te.StringTableElement(name="repo_name", attr="repo_name"),
            te.StringTableElement(name="latest_tag", attr="latest_tag"),
            te.StringTableElement(name="branch", attr="branch"),
            te.DateTimeTableElement(name="commit_hash", attr="commit_hash"),
            te.StringTableElement(name="author", attr="author"),
            te.StringTableElement(name="commit_date", attr="commit_date"),
            te.StringTableElement(name="remote_url", attr="remote_url"),
            te.StringTableElement(name="commit_count", attr="commit_count"),
            te.BooleanTableElement(name="is_clean", attr="is_clean"),
        )


class ReleaseVersionsManager(MontrekDataFrameTableManager):
    @property
    def table_elements(self) -> TableElementsType:
        return (
            te.StringTableElement(name="repo_name", attr="repo_name"),
            te.StringTableElement(name="ref", attr="ref"),
            te.StringTableElement(name="commit_hash", attr="commit_hash"),
            te.StringTableElement(name="remote_url", attr="remote_url"),
        )


class InfoVersionsManager(MontrekReportManager):
    document_title = "Montrek Versions"
    git_info_class = GitInfo

    def get_release_info(self) -> ReleaseInfo:
        # The image build writes release.json next to manage.py and the
        # image marker one level up (/montrek/.montrek-image).
        base_dir = Path(settings.BASE_DIR)
        return ReleaseInfo(
            base_dir / "release.json", base_dir.parent / ".montrek-image"
        )

    def collect_report_elements(self) -> None:
        release_info = self.get_release_info()
        if release_info.exists():
            self.append_report_element(self.get_release_versions(release_info))
        else:
            self.append_report_element(self.get_git_versions())

    def get_release_versions(
        self, release_info: ReleaseInfo
    ) -> MontrekDataFrameTableManager:
        session_data = self.session_data | {
            "df_data": release_info.to_dataframe().to_dict(orient="records")
        }
        return ReleaseVersionsManager(session_data)

    def get_git_versions(self) -> MontrekDataFrameTableManager:
        installed_repo_paths = self._get_installed_repo_paths()
        git_versions_df = self.git_info_class(".").to_dataframe()
        for repo_path in installed_repo_paths:
            git_versions_df = pd.concat(
                [git_versions_df, self.git_info_class(repo_path).to_dataframe()]
            )
        session_data = self.session_data | {
            "df_data": git_versions_df.to_dict(orient="records")
        }
        return GitVersionsManager(session_data)

    def _get_installed_repo_paths(self) -> list[str]:
        apps = settings.MONTREK_EXTENSION_APPS
        repos = []
        for app in apps:
            if "." not in app:
                continue
            repo = app.split(".")[0]
            if repo not in repos and repo.startswith("mt_"):
                repos.append(repo)
        return repos
