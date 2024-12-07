from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.position_managers import PositionTableManager
from showcase.forms.position_forms import PositionCreateForm
from showcase.pages.product_pages import SProductPage


class PositionCreateView(MontrekCreateView):
    manager_class = PositionTableManager
    page_class = SProductPage
    tab = "tab_position_list"
    form_class = PositionCreateForm
    success_url = "position_list"
    title = "Position Create"


class PositionUpdateView(MontrekUpdateView):
    manager_class = PositionTableManager
    page_class = SProductPage
    tab = "tab_position_list"
    form_class = PositionCreateForm
    success_url = "position_list"
    title = "Position Update"


class PositionDeleteView(MontrekDeleteView):
    manager_class = PositionTableManager
    page_class = SProductPage
    tab = "tab_position_list"
    success_url = "position_list"
    title = "Position Delete"


class PositionListView(MontrekListView):
    manager_class = PositionTableManager
    page_class = SProductPage
    tab = "tab_position_list"
    title = "Position List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("position_create"),
            action_id="id_create_position",
            hover_text="Create new Position",
        )
        return (action_new,)
