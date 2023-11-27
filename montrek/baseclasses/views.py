from django.shortcuts import render
from django.views.generic.list import ListView
from baseclasses.dataclasses.nav_bar_model import NavBarModel
from baseclasses.pages import NoAppPage

# Create your views here.


def home(request):
    return render(request, "home.html")


def under_construction(request):
    return render(request, "under_construction.html")


def navbar(request):
    nav_apps = [NavBarModel("account"), NavBarModel("credit_institution")]
    return render(request, "navbar.html", {"nav_apps": nav_apps})


class MontrekListView(ListView):
    template_name = "montrek_table_new.html"
    page = NoAppPage()
    tab = "empty_tab"
    title = "No Title set!"

    @property
    def table_elements(self) -> list:
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.page.page_title
        self.page.set_active_tab(self.tab)
        context["tab_elements"] = self.page.tabs
        context["table_elements"] = self.table_elements
        context['title'] = self.title
        return context
