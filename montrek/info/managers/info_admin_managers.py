import pandas as pd
from django.conf import settings

from baseclasses.typing import TableElementsType
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.managers.montrek_table_manager import MontrekDataFrameTableManager


class AdminLinksManager(MontrekDataFrameTableManager):
    @property
    def table_elements(self) -> TableElementsType:
        return (
            te.StringTableElement(name="System", attr="system"),
            te.StringTableElement(name="Description", attr="description"),
            te.ExternalLinkTableElement(name="Link", attr="link"),
        )


class InfoAdminManager(MontrekReportManager):
    document_title = "Montrek Versions"

    def collect_report_elements(self) -> None:
        self.append_report_element(self.get_admin_links())

    def get_admin_links(self):
        deploy_host = settings.DEPLOY_HOST
        project_name = settings.PROJECT_NAME
        django_admin_link = f"https://{project_name}.{deploy_host}/admin"
        keycloak_link = f"https://auth.{project_name}.{deploy_host}"
        flower_link = f"https://flower.{project_name}.{deploy_host}"
        admin_links_df = pd.DataFrame(
            {
                "system": ["Django Admin", "Keycloak", "Flower"],
                "description": [
                    "User Management & Scheduling",
                    "Authentification",
                    "Task Monitoring",
                ],
                "link": [django_admin_link, keycloak_link, flower_link],
            }
        )
        session_data = self.session_data | {
            "df_data": admin_links_df.to_dict(orient="records")
        }
        return AdminLinksManager(session_data)
