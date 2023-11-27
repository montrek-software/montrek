from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic import DetailView
from baseclasses.dataclasses.nav_bar_model import NavBarModel
from baseclasses.pages import NoAppPage, NoPage

# Create your views here.


def home(request):
    return render(request, "home.html")


def under_construction(request):
    return render(request, "under_construction.html")


def navbar(request):
    nav_apps = [NavBarModel("account"), NavBarModel("credit_institution")]
    return render(request, "navbar.html", {"nav_apps": nav_apps})


class MontrekPageViewMixin:
    def get_page_context(self, context, **kwargs):
        context["page_title"] = self.page.page_title
        self.page.set_active_tab(self.tab)
        context["tab_elements"] = self.page.tabs
        context["title"] = self.title
        return context


class MontrekListView(ListView, MontrekPageViewMixin):
    template_name = "montrek_table_new.html"
    page = NoAppPage()
    tab = "empty_tab"
    title = "No Title set!"

    @property
    def table_elements(self) -> list:
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        context["table_elements"] = self.table_elements
        return context


class MontrekDetailView(DetailView, MontrekPageViewMixin):
    template_name = "montrek_details.html"
    page_class = NoPage
    tab = "empty_tab"
    title = "No Title set!"

    @property
    def detail_elements(self) -> list:
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.page = self.page_class(context["object"])
        context = self.get_page_context(context, **kwargs)
        context["detail_elements"] = self.detail_elements
        return context
