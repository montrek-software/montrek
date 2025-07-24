import pandas as pd
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.managers.montrek_table_manager import MontrekDataFrameTableManager


class AdminLinksManager(MontrekDataFrameTableManager): ...


class InfoAdminManager(MontrekReportManager):
    document_title = "Montrek Versions"

    def collect_report_elements(self) -> None:
        self.append_report_element(self.get_admin_links())

    def get_admin_links(self):
        admin_links_df = pd.DataFrame()
        session_data = self.session_data | {
            "df_data": admin_links_df.to_dict(orient="records")
        }
        return AdminLinksManager(session_data)
