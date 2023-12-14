from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from baseclasses.dataclasses.nav_bar_model import NavBarModel
from baseclasses.pages import NoPage
from baseclasses.forms import DateRangeForm
from baseclasses.forms import MontrekCreateForm
from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses import utils

# Create your views here.


def home(request):
    return render(request, "home.html")


def under_construction(request):
    return render(request, "under_construction.html")


def navbar(request):
    nav_apps = [NavBarModel("account"), NavBarModel("credit_institution")]
    return render(request, "navbar.html", {"nav_apps": nav_apps})


class MontrekPageViewMixin:
    page_class = NoPage
    tab = "empty_tab"
    title = "No Title set!"
    def get_page_context(self, context, **kwargs):
        page = self.page_class(self.request, **self.kwargs)
        context["page_title"] = page.page_title
        page.set_active_tab(self.tab)
        context["tab_elements"] = page.tabs
        context["title"] = self.title
        context["show_date_range_selector"] = page.show_date_range_selector
        context.update(self._handle_date_range_form())
        return context

    def _handle_date_range_form(self):
        start_date, end_date = utils.get_date_range_dates(self.request)
        # Get dates from form if new were submitted or take from session
        request_get = self.request.GET.copy()
        request_get = (
            request_get
            if "start_date" in request_get and "end_date" in request_get
            else None
        )
        date_range_form = DateRangeForm(
            request_get or {"start_date": start_date, "end_date": end_date}
        )
        if date_range_form.is_valid():
            start_date = date_range_form.cleaned_data["start_date"]
            end_date = date_range_form.cleaned_data["end_date"]
            self.request.session["start_date"] = start_date.strftime("%Y-%m-%d")
            self.request.session["end_date"] = end_date.strftime("%Y-%m-%d")
        return {"date_range_form": date_range_form}


class StdQuerysetMixin:
    @property
    def elements(self) -> list:
        return []

    def _get_std_queryset(self):
        return self.repository(self.request).std_queryset()


class MontrekTemplateView(TemplateView, MontrekPageViewMixin):
    template_name = "montrek.html"
    repository = MontrekRepository

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        template_context = self.get_template_context()
        context.update(template_context)
        return context

    def get_template_context(self) -> dict:
        raise NotImplementedError("Please implement this method in your subclass!")

class MontrekListView(ListView, MontrekPageViewMixin, StdQuerysetMixin):
    template_name = "montrek_table.html"
    repository = MontrekRepository

    def get_queryset(self):
        return self._get_std_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        context["table_elements"] = self.elements
        return context


class MontrekDetailView(DetailView, MontrekPageViewMixin, StdQuerysetMixin):
    template_name = "montrek_details.html"
    repository = MontrekRepository

    def get_queryset(self):
        return self._get_std_queryset()


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        context["detail_elements"] = self.elements
        return context

class MontrekCreateView(CreateView, StdQuerysetMixin):
    repository = MontrekRepository
    form_class = MontrekCreateForm

    def get_queryset(self):
        return self._get_std_queryset()
