from baseclasses.typing import SessionDataType
from docs_framework.managers.docs_managers import DocsManager
from docs_framework.mixins.docs_mixins import DocsFilesMixin
from reporting.views import MontrekReportView


class DocsViewABC(MontrekReportView, DocsFilesMixin):
    manager_class = DocsManager

    @property
    def session_data(self) -> SessionDataType:
        session_data = super().session_data
        session_data["docs_file"] = self.get_docs_file_by_name(
            session_data["docs_name"]
        )
        session_data["docs_file_path"] = session_data["docs_file"].docs_path
        return session_data

    @property
    def tab(self) -> str:
        docs_file = self.session_data["docs_file"]
        return f"tab_docs_{docs_file.docs_name}"
