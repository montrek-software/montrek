from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekDetailView, MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.scompany_managers import (
    SCompanyDetailsManager,
    SCompanyTableManager,
)
from showcase.pages.scompany_pages import SCompanyDetailsPage, SCompanyPage
from showcase.forms.scompany_forms import SCompanyCreateForm


class SCompanyCreateView(MontrekCreateView):
    manager_class = SCompanyTableManager
    page_class = SCompanyPage
    tab = "tab_scompany_list"
    form_class = SCompanyCreateForm
    success_url = "scompany_list"
    title = "SCompany Create"


class SCompanyUpdateView(MontrekUpdateView):
    manager_class = SCompanyTableManager
    page_class = SCompanyPage
    tab = "tab_scompany_list"
    form_class = SCompanyCreateForm
    success_url = "scompany_list"
    title = "SCompany Update"


class SCompanyDeleteView(MontrekDeleteView):
    manager_class = SCompanyTableManager
    page_class = SCompanyPage
    tab = "tab_scompany_list"
    success_url = "scompany_list"
    title = "SCompany Delete"


class SCompanyListView(MontrekListView):
    manager_class = SCompanyTableManager
    page_class = SCompanyPage
    tab = "tab_scompany_list"
    title = "SCompany List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("scompany_create"),
            action_id="id_create_scompany",
            hover_text="Create new SCompany",
        )
        return (action_new,)


class SCompanyDetailView(MontrekDetailView):
    manager_class = SCompanyDetailsManager
    page_class = SCompanyDetailsPage
    tab = "tab_scompany_details"
    title = "Company Details"
