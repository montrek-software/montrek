from baseclasses.views import MontrekListView
from showcase.managers.sposition_managers import SPositionTableManager
from showcase.pages.sproduct_pages import SProductPage


class SPositionListView(MontrekListView):
    manager_class = SPositionTableManager
    page_class = SProductPage
    tab = "tab_sposition_list"
    title = "Position List"
