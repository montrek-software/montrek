from reporting.views import MontrekReportView
from info.pages import InfoPage
from info.managers.info_versions_managers import InfoVersionsManager
from info.managers.info_admin_managers import InfoAdminManager


class InfoVersionsView(MontrekReportView):
    page_class = InfoPage
    manager_class = InfoVersionsManager
    tab = "id_info"


class InfoAdminView(MontrekReportView):
    page_class = InfoPage
    manager_class = InfoAdminManager
    tab = "id_admin"
