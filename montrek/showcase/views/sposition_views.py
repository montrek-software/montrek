from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.sposition_managers import SPositionTableManager
from showcase.forms.sposition_forms import SPositionCreateForm
from showcase.pages.sproduct_pages import SProductPage


class SPositionCreateView(MontrekCreateView):
    manager_class = SPositionTableManager
    page_class = SProductPage
    tab = "tab_sposition_list"
    form_class = SPositionCreateForm
    success_url = "sposition_list"
    title = "SPosition Create"


class SPositionUpdateView(MontrekUpdateView):
    manager_class = SPositionTableManager
    page_class = SProductPage
    tab = "tab_sposition_list"
    form_class = SPositionCreateForm
    success_url = "sposition_list"
    title = "SPosition Update"


class SPositionDeleteView(MontrekDeleteView):
    manager_class = SPositionTableManager
    page_class = SProductPage
    tab = "tab_sposition_list"
    success_url = "sposition_list"
    title = "SPosition Delete"


class SPositionListView(MontrekListView):
    manager_class = SPositionTableManager
    page_class = SProductPage
    tab = "tab_sposition_list"
    title = "SPosition List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("sposition_create"),
            action_id="id_create_position",
            hover_text="Create new SPosition",
        )
        return (action_new,)
