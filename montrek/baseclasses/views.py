import os
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Page
from django.shortcuts import render
from django.views.generic.list import ListView
from django.core.paginator import Paginator
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views import View
from django.http import HttpResponseRedirect
from django.http import HttpResponse, Http404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from decouple import config
from baseclasses.dataclasses.nav_bar_model import NavBarModel
from baseclasses.dataclasses.link_model import LinkModel
from reporting.dataclasses.table_elements import (
    AttrTableElement,
    LinkTextTableElement,
    TableElement,
)
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.pages import NoPage
from baseclasses.forms import DateRangeForm, FilterForm
from baseclasses.forms import MontrekCreateForm
from baseclasses import utils
from baseclasses.dataclasses.history_data_table import HistoryDataTable
from baseclasses.managers.montrek_manager import MontrekManagerNotImplemented
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.managers.montrek_report_manager import LatexReportManager

# Create your views here.


def home(request):
    return render(request, "home.html")


def under_construction(request):
    return render(request, "under_construction.html")


def navbar(request):
    navbar_apps_config = config("NAVBAR_APPS", default="").split(" ")
    navbar_apps = [NavBarModel(app) for app in navbar_apps_config if app != ""]
    return render(request, "navbar.html", {"nav_apps": navbar_apps})


def links(request):
    links_config = config("LINKS", default="http://example.com,Example").split(" ")
    links = []
    for link in links_config:
        link_constituents = link.split(",")
        links.append(LinkModel(href=link_constituents[0], title=link_constituents[1]))
    return render(request, "links.html", {"links": links})


def client_logo(request):
    client_logo_path = config("CLIENT_LOGO_PATH", default="")
    return render(request, "client_logo.html", {"client_logo_path": client_logo_path})


class MontrekPageViewMixin:
    page_class = NoPage
    tab = "empty_tab"
    title = "No Title set!"
    request = None

    @property
    def actions(self) -> tuple[ActionElement] | tuple:
        return ()

    def get_page_context(self, context, **kwargs):
        page = self.page_class(**self.kwargs)
        context["page_title"] = page.page_title
        page.set_active_tab(self.tab)
        context["tab_elements"] = page.tabs
        context["actions"] = self.actions
        context["title"] = self.title
        context["show_date_range_selector"] = page.show_date_range_selector
        context.update(self._handle_date_range_form())
        return context

    def _handle_date_range_form(self):
        if not self.request:
            return {}
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
    _manager = None
    request = None

    @property
    def manager(self):
        if self._manager is None:
            self._manager = self.manager_class(self.session_data)
        return self._manager

    # TODO:
    ##Should go to manager
    @property
    def elements(self) -> list[TableElement]:
        return []

    def get_fields_from_elements(self) -> list[str]:
        link_elements = self.get_link_table_elements(self.elements)
        att_elements = self.get_attr_table_elements(self.elements)
        return [element.text for element in link_elements] + [
            element.attr for element in att_elements
        ]

    def get_attr_table_elements(self, elements) -> list[AttrTableElement]:
        return [
            element for element in elements if isinstance(element, AttrTableElement)
        ]

    def get_link_table_elements(self, elements) -> list[LinkTextTableElement]:
        return [
            element for element in elements if isinstance(element, LinkTextTableElement)
        ]

    ##

    @property
    def session_data(self) -> dict:
        if not self.request:
            return {}
        session_data = dict(self.request.GET)
        kwargs = getattr(self, "kwargs", {})
        session_data.update(kwargs)
        session_data.update(dict(self.request.session))
        session_data.update(self._get_filters(session_data))
        if self.request.user.is_authenticated:
            session_data["user_id"] = self.request.user.id
        return session_data

    def _get_filters(self, session_data):
        filter_field = session_data.pop("filter_field", [])
        filter_negate = session_data.pop("filter_negate", [])
        filter_lookup = session_data.pop("filter_lookup", [])
        filter_value = session_data.pop("filter_value", [])
        filter_data = {
            "filter_field": filter_field,
            "filter_negate": filter_negate,
            "filter_lookup": filter_lookup,
            "filter_value": ",".join(filter_value),
        }
        if filter_field and filter_lookup and filter_value:
            true_values = ("True", True, 1, "1")
            false_values = ("False", False, 0, "0")
            filter_negate = filter_negate[0] in true_values
            filter_field = f"{filter_field[0]}__{filter_lookup[0]}"
            if filter_value in true_values:
                filter_value = True
            elif filter_value in false_values:
                filter_value = False
            else:
                filter_value = filter_value[0]
            filter_data["filter_negate"] = filter_negate
            filter_data["filter"] = {filter_field: filter_value}
        return filter_data

    def show_messages(self):
        for message in self.manager.messages:
            if message.message_type == "error":
                messages.error(self.request, message.message)
            elif message.message_type == "info":
                messages.info(self.request, message.message)

    def get_view_queryset(self):
        return self.manager.repository.std_queryset()


class MontrekPermissionRequiredMixin(PermissionRequiredMixin):
    permission_required = []

    def handle_no_permission(self):
        # handled by PermissionErrorMiddleware
        raise PermissionDenied


class MontrekTemplateView(
    MontrekPermissionRequiredMixin, TemplateView, MontrekPageViewMixin, MontrekViewMixin
):
    template_name = "montrek.html"
    manager_class = MontrekManagerNotImplemented

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not hasattr(self, "kwargs"):
            self.kwargs = kwargs
        context = self.get_page_context(context, **kwargs)
        template_context = self.get_template_context()
        context.update(template_context)
        return context

    def get_template_context(self) -> dict:
        raise NotImplementedError("Please implement this method in your subclass!")

    def get_queryset(self):
        return self.get_view_queryset()


class MontrekListView(
    MontrekPermissionRequiredMixin, ListView, MontrekPageViewMixin, MontrekViewMixin
):
    template_name = "montrek_table.html"
    manager_class = MontrekManagerNotImplemented

    def get(self, request, *args, **kwargs):
        if self.request.GET.get("gen_csv") == "true":
            return self.list_to_csv()
        if self.request.GET.get("gen_pdf") == "true":
            return self.list_to_pdf()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.get_view_queryset()
        page_number = self.session_data.get("page", [1])[0]
        paginate_by = 10  # or you can make this customizable
        paginator = Paginator(queryset, paginate_by)
        page = paginator.get_page(page_number)
        return page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        self.show_messages()
        if not isinstance(self.manager, MontrekTableManager):
            raise ValueError("Manager must be of type MontrekTableManager")
        context["table"] = self.manager.to_html()
        context["filter_form"] = FilterForm(
            self.session_data,
            filter_field_choices=self.manager.get_satellite_field_choices(),
        )
        return context

    def list_to_csv(self):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="export.csv"'
        return self.manager.download_csv(response)

    def list_to_pdf(self):
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="export.pdf"'
        report_manager = LatexReportManager(self.session_data)
        report_manager.append_report_element(self.manager)
        pdf_path = report_manager.compile_report()
        self.manager.messages += report_manager.messages
        self.show_messages()
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type="application/pdf")
                response["Content-Disposition"] = (
                    "inline; filename=" + os.path.basename(pdf_path)
                )
                return response
        previous_url = self.request.META.get("HTTP_REFERER")
        return HttpResponseRedirect(previous_url)


class MontrekHistoryListView(MontrekTemplateView):
    template_name = "montrek_history.html"

    def get_template_context(self) -> dict:
        history_querysets = self.manager.repository.get_history_queryset(
            pk=self.kwargs["pk"]
        )

        return {
            "history_data_tables": [
                HistoryDataTable(title=queryset, queryset=history_querysets[queryset])
                for queryset in history_querysets
            ]
        }


class MontrekDetailView(
    MontrekPermissionRequiredMixin, DetailView, MontrekPageViewMixin, MontrekViewMixin
):
    template_name = "montrek_details.html"
    manager_class = MontrekManagerNotImplemented

    def get_queryset(self):
        return self.get_view_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        context["detail_elements"] = self.elements
        return context


class MontrekCreateUpdateView(
    MontrekPermissionRequiredMixin, CreateView, MontrekPageViewMixin, MontrekViewMixin
):
    manager_class = MontrekManagerNotImplemented
    form_class = MontrekCreateForm
    template_name = "montrek_create.html"
    success_url = "under_construction"
    title = ""

    def get_queryset(self):
        return self.get_view_queryset()

    def get_success_url(self):
        return reverse(self.success_url)

    def form_valid(self, form):
        self.manager.create_object(data=form.cleaned_data)
        return HttpResponseRedirect(self.get_success_url())

    def get_form(self, form_class=None):
        # TODO: Form should receive manager
        return self.form_class(repository=self.manager.repository)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        return context

    def post(self, request, *args, **kwargs):
        # TODO: Form should receive manager
        form = self.form_class(self.request.POST, repository=self.manager.repository)
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class MontrekCreateView(MontrekCreateUpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Create"
        return context


class MontrekUpdateView(MontrekCreateUpdateView):
    def get_form(self, form_class=None):
        initial = self.manager.get_object_from_pk_as_dict(self.kwargs["pk"])

        return self.form_class(repository=self.manager.repository, initial=initial)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Update"
        return context


class MontrekDeleteView(
    View, MontrekPermissionRequiredMixin, MontrekViewMixin, MontrekPageViewMixin
):
    manager_class = MontrekManagerNotImplemented
    success_url = "under_construction"
    template_name = "montrek_delete.html"

    def get_success_url(self):
        return reverse(self.success_url)

    def post(self, request, *args, **kwargs):
        if "action" in request.POST and request.POST["action"] == "Delete":
            self.manager.delete_object(pk=self.kwargs["pk"])
        return HttpResponseRedirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"pk": self.kwargs["pk"]})
