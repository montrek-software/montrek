import pandas as pd
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.managers.montrek_table_manager import MontrekDataFrameTableManager
from reporting.dataclasses import table_elements as te
from info.modules.git_info import GitInfo


class GitVersionsManager(MontrekDataFrameTableManager):
    @property
    def table_elements(self) -> tuple[te.TableElement, ...]:
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


class InfoVersionsManager(MontrekReportManager):
    document_title = "Montrek Versions"

    def collect_report_elements(self) -> None:
        self.append_report_element(self.get_git_versions())

    def get_git_versions(self) -> MontrekDataFrameTableManager:
        git_versions_df = GitInfo(".").to_dataframe()
        session_data = self.session_data | {
            "df_data": git_versions_df.to_dict(orient="records")
        }
        return GitVersionsManager(session_data)
