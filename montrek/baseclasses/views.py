import os
from typing import Any

from decouple import config
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from reporting.dataclasses.table_elements import (
    AttrTableElement,
    LinkTextTableElement,
    TableElement,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.managers.montrek_table_manager import MontrekTableManager

from baseclasses import utils
from baseclasses.dataclasses.history_data_table import HistoryDataTable
from baseclasses.dataclasses.link_model import LinkModel
from baseclasses.dataclasses.nav_bar_model import NavBarDropdownModel, NavBarModel
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.forms import DateRangeForm, FilterForm, MontrekCreateForm
from baseclasses.managers.montrek_manager import MontrekManagerNotImplemented
from baseclasses.pages import NoPage

from file_upload.forms import SimpleUploadFileForm
from file_upload.managers.simple_upload_file_manager import SimpleUploadFileManager
from baseclasses.serializers import MontrekSerializer


def home(request):
    return render(request, "home.html")


def under_construction(request):
    return render(request, "under_construction.html")


def navbar(request):
    navbar_apps_config = config("NAVBAR_APPS", default="").split(",")
    navbar_apps = []
    navbar_dropdowns = {}
    for app in navbar_apps_config:
        if app == "":
            continue
        app_structure = app.split(".")
        if len(app_structure) > 1:
            repo_name = app_structure[0]
            app_name = app_structure[1]
            if repo_name not in navbar_dropdowns:
                navbar_dropdowns[repo_name] = NavBarDropdownModel(repo_name)
            dropdown = navbar_dropdowns[repo_name]
            dropdown.dropdown_items.append(NavBarModel(app_name))
        else:
            navbar_apps.append(NavBarModel(app))
    return render(
        request,
        "navbar.html",
        {"nav_apps": navbar_apps, "navbar_dropdowns": navbar_dropdowns.values()},
    )


def links(request):
    links_config = config("LINKS", default="http://example.com,Example").split(" ")
    links = []
    for link in links_config:
        link_constituents = link.split(",")
        links.append(LinkModel(href=link_constituents[0], title=link_constituents[1]))
    return render(request, "links.html", {"links": links})


def test_banner(request):
    test_tag = config("DEBUG", default=0)
    test_tag = True if test_tag == "1" else False
    return render(request, "test_banner.html", {"test_tag": test_tag})


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

    @property
    def session_data(self) -> dict:
        session_data = dict(self.request.GET)
        kwargs = getattr(self, "kwargs", {})
        session_data.update(kwargs)
        session_data.update(dict(self.request.session))
        session_data["request_path"] = self.request.path
        session_data.update(self._get_filters(session_data))
        if self.request.user.is_authenticated:
            session_data["user_id"] = self.request.user.id
        self.request.session["filter"] = session_data.get("filter", {})
        session_data["host_url"] = self.request.build_absolute_uri("/")[:-1]
        return session_data

    def _get_filters(self, session_data):
        request_path = self.request.path
        filter_field = session_data.pop("filter_field", [""])[0]
        filter_negate = session_data.pop("filter_negate", [""])[0]
        filter_lookup = session_data.pop("filter_lookup", [""])[0]
        filter_value = session_data.pop("filter_value", [""])[0]
        filter_data = {}
        if filter_lookup == "isnull":
            filter_value = True
        if filter_field:
            true_values = ("True", "true", True)
            false_values = ("False", "false", False)
            filter_negate = filter_negate in true_values
            filter_lookup = filter_lookup
            filter_value = filter_value
            filter_key = f"{filter_field}__{filter_lookup}"
            if filter_lookup == "in":
                filter_value = filter_value.split(",")
            if filter_value in true_values:
                filter_value = True
            elif filter_value in false_values:
                filter_value = False
            filter_data["filter"] = {}
            filter_data["filter"][request_path] = {
                filter_key: {
                    "filter_negate": filter_negate,
                    "filter_value": filter_value,
                }
            }
        return filter_data

    def show_messages(self):
        self.manager.collect_messages()
        for message in self.manager.messages:
            if message.message_type == "error":
                messages.error(self.request, message.message)
            elif message.message_type == "info":
                messages.info(self.request, message.message)

    def get_view_queryset(self):
        return self.manager.repository.receive()


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


class ToPdfMixin:
    def list_to_pdf(self):
        response = HttpResponse(content_type="application/pdf")
        report_manager = LatexReportManager(self.manager)
        pdf_path = report_manager.compile_report()
        self.show_messages()
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type="application/pdf")
                response[
                    "Content-Disposition"
                ] = "inline; filename=" + os.path.basename(pdf_path)
                return response
        previous_url = self.request.META.get("HTTP_REFERER")
        return HttpResponseRedirect(previous_url)


class MontrekListView(
    MontrekPermissionRequiredMixin,
    ListView,
    MontrekPageViewMixin,
    MontrekViewMixin,
    ToPdfMixin,
):
    template_name = "montrek_table.html"
    manager_class = MontrekManagerNotImplemented
    do_simple_file_upload = False

    def get(self, request, *args, **kwargs):
        if self.request.GET.get("gen_csv") == "true":
            return self.list_to_csv()
        if self.request.GET.get("gen_excel") == "true":
            return self.list_to_excel()
        if self.request.GET.get("gen_pdf") == "true":
            return self.list_to_pdf()
        if self.request.GET.get("reset_filter") == "true":
            return self.reset_filter()
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
            raise ValueError(
                f"Manager {self.manager.__class__.__name__} must be of type MontrekTableManager"
            )
        context["table"] = self.manager.to_html()
        filter = self.session_data.get("filter", {})
        filter = filter.get(self.session_data["request_path"], {})
        context["filter_form"] = FilterForm(
            filter=filter,
            filter_field_choices=self.manager.get_std_queryset_field_choices(),
        )
        if self.do_simple_file_upload:
            context["simple_upload_form"] = SimpleUploadFileForm(".xlsx,.csv")
        context["do_simple_file_upload"] = self.do_simple_file_upload
        return context

    def list_to_csv(self):
        response = self.manager.download_or_mail_csv()
        self.show_messages()
        return response

    def list_to_excel(self):
        response = self.manager.download_or_mail_excel()
        self.show_messages()
        return response

    def reset_filter(self):
        self.request.session["filter"] = {}
        return HttpResponseRedirect(self.request.path)

    def post(self, request, *args, **kwargs):
        form = SimpleUploadFileForm(".xlsx,.csv", request.POST, request.FILES)
        if form.is_valid():
            session_data = self.session_data.copy()
            session_data["overwrite"] = form.cleaned_data["overwrite"]
            file_upload_manager = SimpleUploadFileManager(
                session_data=session_data,
                **self.kwargs,
            )
            result = file_upload_manager.upload_and_process(request.FILES["file"])
            if result:
                messages.info(
                    request,
                    file_upload_manager.processor.message,
                )
            else:
                messages.error(
                    request,
                    file_upload_manager.processor.message,
                )
        return HttpResponseRedirect(self.request.path)


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
    MontrekPermissionRequiredMixin,
    DetailView,
    MontrekPageViewMixin,
    MontrekViewMixin,
    ToPdfMixin,
):
    """
    View for displaying details of a single entity. pk is the corrresponding hub entity if is_hub_based is True
    """

    template_name = "montrek_details.html"
    manager_class = MontrekManagerNotImplemented
    is_hub_based = True

    def get_queryset(self):
        return self.get_view_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not isinstance(self.manager, MontrekDetailsManager):
            raise ValueError(
                f"Manager {self.manager_class.__name__} must be of type MontrekDetailsManager"
            )
        context = self.get_page_context(context, **kwargs)
        context["table"] = self.manager.to_html()
        return context

    def get(self, request, *args, **kwargs):
        if self.is_hub_based:
            kwargs = self._set_hub_value_date_pk(kwargs)

        if self.request.GET.get("gen_pdf") == "true":
            return self.list_to_pdf()
        return super().get(request, *args, **kwargs)

    def _set_hub_value_date_pk(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        repository = self.manager_class.repository_class()
        hub_value_date_pk = repository.receive().filter(hub__pk=kwargs["pk"]).first().pk
        kwargs["pk"] = hub_value_date_pk
        self.kwargs["pk"] = hub_value_date_pk
        return kwargs


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
        self.object = None
        form = self.form_class(self.request.POST, repository=self.manager.repository)
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_invalid(self, form):
        msg = "\n".join([f"{k}: {', '.join(v)}" for k, v in form.errors.items()])
        messages.error(self.request, msg)
        return super().form_invalid(form)


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
    MontrekPermissionRequiredMixin, TemplateView, MontrekViewMixin, MontrekPageViewMixin
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


class MontrekReportView(MontrekTemplateView, ToPdfMixin):
    manager_class = MontrekReportManager
    template_name = "montrek_report.html"

    def get_template_context(self) -> dict:
        return {"report": self.manager.to_html()}

    def get(self, request, *args, **kwargs):
        if self.request.GET.get("gen_pdf") == "true":
            return self.list_to_pdf()
        return super().get(request, *args, **kwargs)

    @property
    def title(self):
        return self.manager.document_title


class MontrekRestApiView(APIView, MontrekViewMixin):
    manager_class = MontrekManagerNotImplemented

    def get(self, request, *args, **kwargs):
        query = self.get_view_queryset()
        serializer = MontrekSerializer(query, many=True, manager=self.manager)
        return Response(serializer.data, status=status.HTTP_200_OK)
