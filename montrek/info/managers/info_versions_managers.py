import pandas as pd
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.managers.montrek_table_manager import MontrekDataFrameTableManager
from reporting.dataclasses import table_elements as te


class GitVersionsManager(MontrekDataFrameTableManager):
    @property
    def table_elements(self) -> tuple[te.TableElement, ...]:
        return (te.StringTableElement(name="repository", attr="repository"),)


class InfoVersionsManager(MontrekReportManager):
    document_title = "Montrek Versions"

    def collect_report_elements(self) -> None:
        self.append_report_element(self.get_git_versions())

    def get_git_versions(self) -> MontrekDataFrameTableManager:
        git_versions_df = pd.DataFrame({"repository": ["A", "B", "C"]})
        session_data = self.session_data | {
            "df_data": git_versions_df.to_dict(orient="records")
        }
        return GitVersionsManager(session_data)
