from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.forms.models import model_to_dict
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
        page = self.page_class(self.repository_object, **self.kwargs)
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


class MontrekViewMixin:
    @property
    def repository_object(self):
        return self.repository(self.session_data)

    @property
    def elements(self) -> list:
        return []

    @property
    def session_data(self) -> dict:
        session_data = dict(self.request.GET)
        session_data.update(dict(self.request.session))
        return session_data

    def _get_std_queryset(self):
        return self.repository_object.std_queryset()


class MontrekTemplateView(TemplateView, MontrekPageViewMixin, MontrekViewMixin):
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


class MontrekListView(ListView, MontrekPageViewMixin, MontrekViewMixin):
    template_name = "montrek_table.html"
    repository = MontrekRepository

    def get_queryset(self):
        return self._get_std_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        context["table_elements"] = self.elements
        return context


class MontrekDetailView(DetailView, MontrekPageViewMixin, MontrekViewMixin):
    template_name = "montrek_details.html"
    repository = MontrekRepository

    def get_queryset(self):
        return self._get_std_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        context["detail_elements"] = self.elements
        return context


class MontrekCreateEditView(CreateView, MontrekPageViewMixin, MontrekViewMixin):
    repository = MontrekRepository
    form_class = MontrekCreateForm
    template_name = "montrek_create.html"
    success_url = "under_construction"

    def get_queryset(self):
        return self._get_std_queryset()

    def get_success_url(self):
        return reverse(self.success_url)

    def form_valid(self, form):
        self.repository_object.std_create_object(data=form.cleaned_data)
        return HttpResponseRedirect(self.get_success_url())

    def get_form(self):
        return self.form_class(repository=self.repository_object)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.request.POST, repository=self.repository_object)
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class MontrekCreateView(MontrekCreateEditView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Create"
        return context


class MontrekEditView(MontrekCreateEditView):
    def get_form(self):
        edit_object = self.repository_object.std_queryset().get(pk=self.kwargs["pk"])
        initial = self.repository_object.object_to_dict(edit_object)
        return self.form_class(repository=self.repository_object, initial=initial)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Edit"
        return context

class MontrekDeleteView(View, MontrekViewMixin, MontrekPageViewMixin):
    repository = MontrekRepository
    success_url = "under_construction"
    template_name = "montrek_delete.html"

    def get_success_url(self):
        return reverse(self.success_url)

    def post(self, request, *args, **kwargs):
        if 'action' in request.POST and request.POST['action'] == 'Delete':
            delete_object = self.repository_object.std_queryset().get(pk=self.kwargs["pk"])
            self.repository_object.std_delete_object(delete_object)
        return HttpResponseRedirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"pk": self.kwargs["pk"]})
