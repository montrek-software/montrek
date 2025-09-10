from info.forms.app_select_form import AppSelectForm
from info.managers.info_admin_managers import InfoAdminManager
from info.managers.info_db_structure_manager import InfoDbstructureReportManager
from info.managers.info_versions_managers import InfoVersionsManager
from info.pages import InfoPage
from reporting.views import MontrekReportView


class InfoVersionsView(MontrekReportView):
    page_class = InfoPage
    manager_class = InfoVersionsManager
    tab = "id_info"


class InfoAdminView(MontrekReportView):
    page_class = InfoPage
    manager_class = InfoAdminManager
    tab = "id_admin"


class InfoDbStructureView(MontrekReportView):
    page_class = InfoPage
    manager_class = InfoDbstructureReportManager
    report_form_class = AppSelectForm
    tab = "id_db_structure"
