from reporting.views import MontrekReportView
from info.pages import InfoPage
from info.managers.info_versions_managers import InfoVersionsManager


class InfoVersionsView(MontrekReportView):
    page_class = InfoPage
    manager_class = InfoVersionsManager
    tab = "id_info"
