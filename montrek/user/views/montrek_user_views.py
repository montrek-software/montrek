from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekDetailView, MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from user.managers.montrek_user_managers import MontrekUserTableManager
from user.managers.montrek_user_managers import MontrekUserDetailsManager
from user.pages.montrek_user_pages import MontrekUserPage
from user.pages.montrek_user_pages import MontrekUserDetailsPage
from user.forms.montrek_user_forms import MontrekUserCreateForm


class MontrekUserCreateView(MontrekCreateView):
    manager_class = MontrekUserTableManager
    page_class = MontrekUserPage
    tab = "tab_montrek_user_list"
    form_class = MontrekUserCreateForm
    success_url = "montrek_user_list"
    title = "MontrekUser Create"


class MontrekUserUpdateView(MontrekUpdateView):
    manager_class = MontrekUserTableManager
    page_class = MontrekUserPage
    tab = "tab_montrek_user_list"
    form_class = MontrekUserCreateForm
    success_url = "montrek_user_list"
    title = "MontrekUser Update"


class MontrekUserDeleteView(MontrekDeleteView):
    manager_class = MontrekUserTableManager
    page_class = MontrekUserPage
    tab = "tab_montrek_user_list"
    success_url = "montrek_user_list"
    title = "MontrekUser Delete"


class MontrekUserListView(MontrekListView):
    manager_class = MontrekUserTableManager
    page_class = MontrekUserPage
    tab = "tab_montrek_user_list"
    title = "MontrekUser List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("montrek_user_create"),
            action_id="id_create_montrek_user",
            hover_text="Create new MontrekUser",
        )
        return (action_new,)


class MontrekUserDetailView(MontrekDetailView):
    manager_class = MontrekUserDetailsManager
    page_class = MontrekUserDetailsPage
    tab = "tab_montrek_user_details"
    title = "MontrekUser Details"
