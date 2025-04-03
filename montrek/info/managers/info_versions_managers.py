from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.managers.montrek_table_manager import MontrekDataFrameTableManager
from reporting.dataclasses import table_elements as te


class GitVersionsManager(MontrekDataFrameTableManager):
    @property
    def table_elements(self) -> tuple[te.TableElement, ...]:
        return (te.StringTableElement(name="A", attr="A"),)


class InfoVersionsManager(MontrekReportManager):
    def collect_report_elements(self) -> None:
        self.append_report_element(self.get_git_versions())

    def get_git_versions(self) -> MontrekDataFrameTableManager:
        session_data = self.session_data.copy()
        session_data["df_data"] = {"A": [1, 2, 3]}
        return GitVersionsManager(session_data)
