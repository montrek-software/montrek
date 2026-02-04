import logging
import os
from typing import Any, BinaryIO, Protocol

from baseclasses import utils
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.forms import DateRangeForm, FilterForm, MontrekCreateForm
from baseclasses.managers.montrek_manager import MontrekManagerNotImplemented
from baseclasses.pages import NoPage
from baseclasses.sanitizer import HtmlSanitizer
from baseclasses.serializers import MontrekSerializer
from baseclasses.typing import SessionDataType
from baseclasses.utils import TableMetaSessionData, get_content_type
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_safe
from django.views.generic import DetailView, RedirectView, View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from file_upload.forms import SimpleUploadFileForm
from file_upload.managers.simple_upload_file_manager import SimpleUploadFileManager
from info.managers.download_registry_storage_managers import (
    DownloadRegistryStorageManager,
)
from info.models.download_registry_sat_models import DownloadType
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.managers.montrek_table_manager import (
    HistoryDataTableManager,
    MontrekTableManager,
)
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)


@require_safe
def redirect_home(request):
    redirect_url = settings.HOME_URL
    return redirect(reverse(redirect_url))


@require_safe
def home(request):
    project_name = settings.PROJECT_NAME.replace("mt_", "").replace("_", " ").title()
    return render(request, "home.html", context={"project_name": project_name})


@require_safe
def under_construction(request):
    return render(request, "under_construction.html")


class MontrekPageViewMixin:
    page_class = NoPage
    tab = "empty_tab"
    title = "No Title set!"
    request = None

    @property
    def actions(self) -> tuple[ActionElement] | tuple:
        return ()

    def get_page_context(self, context, **kwargs):
        kwargs.update(self.session_data)
        page = self.page_class(**kwargs)
        context["page_title"] = HtmlSanitizer().clean_html(page.page_title)
        page.set_active_tab(self.tab)
        context["tab_elements"] = page.tabs
        context["actions"] = self.actions
        context["title"] = self.title
        context["show_date_range_selector"] = page.show_date_range_selector
        context["overview"] = page.overview
        context.update(self._handle_date_range_form())
        return context

    def _handle_date_range_form(self) -> dict[str, DateRangeForm]:
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
    _session_data = None

    @property
    def manager(self):
        if self._manager is None:
            self._manager = self.manager_class(self.session_data)
        return self._manager

    @property
    def session_data(self) -> SessionDataType:
        if self._session_data:
            return self._session_data
        session_data = {}
        if self.request.method == "GET":
            session_data.update(dict(self.request.GET))
        elif self.request.method == "POST":
            session_data.update(dict(self.request.POST))
        kwargs = getattr(self, "kwargs", {})
        session_data.update(kwargs)
        session_data.update(dict(self.request.session))
        session_data["request_path"] = self.request.path
        if self.request.user.is_authenticated:
            session_data["user_id"] = self.request.user.id
        session_data["host_url"] = self.request.build_absolute_uri("/")[:-1]
        session_data["http_referer"] = self.request.META.get("HTTP_REFERER")
        session_data = self.view_dependent_session_data(session_data)
        self._session_data = session_data
        return session_data

    def view_dependent_session_data(
        self, session_data: SessionDataType
    ) -> SessionDataType:
        return session_data

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


class ToPdfMixin:
    def list_to_pdf(self):
        report_manager = LatexReportManager(self.manager)
        pdf_path = report_manager.compile_report()
        self.show_messages()
        if pdf_path and os.path.exists(pdf_path):
            DownloadRegistryStorageManager(
                self.session_data
            ).store_in_download_registry(self.manager.document_name, DownloadType.PDF)
            return FileResponse(
                self.open_file(pdf_path),
                content_type="application/pdf",
                filename=os.path.basename(pdf_path),
            )
        previous_url = self.request.META.get("HTTP_REFERER")
        return HttpResponseRedirect(previous_url)

    def open_file(self, path: str) -> BinaryIO:
        return open(path, "rb")  # noqa: SIM115    FileResponse needs the file open


class MontrekApiViewMixin(APIView):
    permission_classes = [AllowAny]

    def _is_rest(self, request) -> bool:
        return request.GET.get("gen_rest_api") == "true"

    def dispatch(self, request, *args, **kwargs):
        if self._is_rest(request):
            # Use DRF's dispatch (this will run JWT auth/DRF permissions)
            return APIView.dispatch(self, request, *args, **kwargs)
        # Non-REST: fall back to the normal Django CBV chain
        return super(APIView, self).dispatch(request, *args, **kwargs)

    # Runs only when APIView.dispatch is used.
    # After DRF has authenticated, run the Django permission check too.
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)  # JWT auth, DRF perms, throttles
        # If this view also mixes in PermissionRequiredMixin, enforce it here.
        if (
            isinstance(self, PermissionRequiredMixin) and not self.has_permission()
        ):  # from PermissionRequiredMixin
            raise PermissionDenied

    # Only used on the REST path (because non-REST doesn't hit APIView.dispatch)
    def get_authenticators(self):
        if self._is_rest(self.request):
            return [JWTAuthentication()]
        return []  # not used outside REST

    def get_permissions(self):
        if self._is_rest(self.request):
            # DRF auth gate; Django perms enforced in .initial() above
            return [IsAuthenticated()]
        return [AllowAny()]


class MontrekListView(
    MontrekApiViewMixin,
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
        q = request.GET
        response = None

        if q.get("gen_csv") == "true":
            response = self.list_to_csv()
        elif q.get("gen_excel") == "true":
            response = self.list_to_excel()
        elif q.get("gen_pdf") == "true":
            response = self.list_to_pdf()
        elif self._is_rest(request):
            response = self.list_to_rest_api()
        elif q.get("refresh_data") == "true":
            response = self.refresh_data()
        elif q.get("action") == "reset":
            response = self.reset_filter()
        elif q.get("action") == "add_filter":
            response = self.add_filter()
        elif q.get("action") == "add_paginate_by":
            response = self.add_paginate_by()
        elif q.get("action") == "sub_paginate_by":
            response = self.sub_paginate_by()
        elif q.get("action") == "is_compact_format_true":
            response = self.set_is_compact_format(True)
        elif q.get("action") == "is_compact_format_false":
            response = self.set_is_compact_format(False)
        elif "order_action" in q:
            response = self.set_order_field(q.get("order_action"))

        return response or super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.manager.get_table()

    def view_dependent_session_data(
        self, session_data: SessionDataType
    ) -> SessionDataType:
        table_meta_session_data = TableMetaSessionData(self.request)
        return table_meta_session_data.update_session_data(session_data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        self.show_messages()
        if not isinstance(self.manager, MontrekTableManager):
            raise ValueError(
                f"Manager {self.manager.__class__.__name__} must be of type MontrekTableManager"
            )
        table = self.manager.to_html()
        context["table"] = table
        context["paginator"] = self.manager.paginator
        context["paginate_by"] = self.manager.paginate_by
        context["is_large"] = self.manager.is_large
        context["is_compact_format"] = self.manager.is_current_compact_format
        session_filter = self.session_data.get("filter", {})
        session_filter = session_filter.get(self.session_data["request_path"], {})
        filter_count = self.session_data.get("filter_count", {})
        filter_count = filter_count.get(self.session_data["request_path"], 1)
        context["filter_forms"] = [
            FilterForm(
                filter=session_filter,
                filter_field_choices=self.manager.get_std_queryset_field_choices(),
                filter_index=i,
            )
            for i in range(filter_count)
        ]
        if self.do_simple_file_upload:
            context["upload_form"] = SimpleUploadFileForm(".xlsx,.csv")

        context["do_simple_file_upload"] = self.do_simple_file_upload
        return context

    def list_to_csv(self):
        DownloadRegistryStorageManager(self.session_data).store_in_download_registry(
            self.manager.document_name, DownloadType.CSV
        )
        response = self.manager.download_or_mail_csv()
        self.show_messages()
        return response

    def list_to_excel(self):
        DownloadRegistryStorageManager(self.session_data).store_in_download_registry(
            self.manager.document_name, DownloadType.XLSX
        )
        response = self.manager.download_or_mail_excel()
        self.show_messages()
        return response

    def list_to_rest_api(self):
        DownloadRegistryStorageManager(self.session_data).store_in_download_registry(
            self.manager.document_name, DownloadType.API
        )
        query = self.manager.to_json()
        serializer = MontrekSerializer(query, manager=self.manager, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def refresh_data(self):
        self.manager.refresh_data_task.delay()
        return HttpResponseRedirect(self.request.path)

    def reset_filter(self):
        request_path = self.session_data["request_path"]
        self.request.session["filter"][request_path] = {}
        self.request.session["filter_count"][request_path] = 1
        return HttpResponseRedirect(self.request.path)

    def add_filter(self):
        request_path = self.session_data["request_path"]
        self.request.session["filter_count"][request_path] += 1
        return HttpResponseRedirect(self.request.path)

    def add_paginate_by(self):
        request_path = self.session_data["request_path"]
        self.request.session["paginate_by"][request_path] += 5
        return HttpResponseRedirect(self.request.path)

    def sub_paginate_by(self):
        request_path = self.session_data["request_path"]
        self.request.session["paginate_by"][request_path] -= 5
        return HttpResponseRedirect(self.request.path)

    def set_is_compact_format(self, val: bool):
        request_path = self.session_data["request_path"]
        self.request.session["is_compact_format"][request_path] = val
        return HttpResponseRedirect(self.request.path)

    def set_order_field(self, val: str | None):
        request_path = self.session_data["request_path"]
        request_data = self.request.session
        field = "order_fields"
        current_order_field = request_data.get(field, {}).get(request_path, [])
        if current_order_field and current_order_field[0]:
            if val == current_order_field[0]:
                val = "-" + str(val)
            elif val == current_order_field[0][1:] and current_order_field[0][0] == "-":
                val = None
        self.request.session["pages"][request_path] = ["1"]
        self.request.session[field][request_path] = [val]
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


class MontrekTemplateView(
    MontrekPermissionRequiredMixin, TemplateView, MontrekPageViewMixin, MontrekViewMixin
):
    template_name = "montrek.html"
    manager_class = MontrekManagerNotImplemented

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not hasattr(self, "kwargs"):
            self.kwargs = kwargs
        template_context = self.get_template_context()
        context.update(template_context)
        context = self.get_page_context(context, **kwargs)
        return context

    def get_template_context(self) -> dict:
        raise NotImplementedError("Please implement this method in your subclass!")

    def get_queryset(self):
        return self.get_view_queryset()


class MontrekHistoryListView(MontrekTemplateView):
    template_name = "montrek_history.html"

    def get_template_context(self) -> dict:
        history_querysets = self.manager.repository.get_history_queryset(
            pk=self.kwargs["pk"]
        )

        return {
            "history_data_tables": [
                HistoryDataTableManager(
                    session_data=self.session_data,
                    title=queryset,
                    queryset=history_querysets[queryset],
                )
                for queryset in history_querysets
            ]
        }


class MontrekDetailView(
    MontrekPermissionRequiredMixin,
    DetailView,
    MontrekPageViewMixin,
    MontrekViewMixin,
    ToPdfMixin,
    MontrekApiViewMixin,
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
        request_get = self.request.GET
        if request_get.get("gen_pdf") == "true":
            return self.list_to_pdf()
        if self._is_rest(request):
            return self.list_to_rest_api()
        return super().get(request, *args, **kwargs)

    def _set_hub_value_date_pk(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        hub_value_date_pk = (
            self.manager_class.repository_class.hub_class.objects.all()
            .get(pk=kwargs["pk"])
            .get_hub_value_date()
            .pk
        )
        kwargs["pk"] = hub_value_date_pk
        self.kwargs["pk"] = hub_value_date_pk
        return kwargs

    def list_to_rest_api(self):
        query = self.manager.to_json()
        serializer = MontrekSerializer(query, manager=self.manager)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReturnToSenderProtocol(Protocol):
    do_return_to_referer: bool
    success_url: str
    request: Any


class ReturnToSenderMixin(ReturnToSenderProtocol):
    def get_success_url(self):
        if self.do_return_to_referer:
            return_url = self.request.session.get("return_url")
            if return_url:
                return return_url
        # Fallback: use the configured success_url name.
        return reverse(self.success_url)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if self.do_return_to_referer:
            http_referer = request.META.get("HTTP_REFERER")
            if http_referer:
                request.session["return_url"] = http_referer
        return response


class MontrekCreateUpdateView(
    MontrekPermissionRequiredMixin,
    ReturnToSenderMixin,
    CreateView,
    MontrekPageViewMixin,
    MontrekViewMixin,
):
    manager_class = MontrekManagerNotImplemented
    form_class = MontrekCreateForm
    template_name = "montrek_create.html"
    do_return_to_referer: bool = True
    success_url = "under_construction"
    title = ""

    @property
    def actions(self) -> tuple[ActionElement] | tuple:
        return (
            ActionElement(
                link=self.get_success_url(),
                icon="arrow-left",
                action_id="id_back",
                hover_text="Go back",
            ),
        )

    def get_queryset(self):
        return self.get_view_queryset()

    def form_valid(self, form):
        self.object = self.manager.create_object(data=form.cleaned_data)
        self.show_messages()
        return HttpResponseRedirect(self.get_success_url())

    def get_form(self, form_class=None):
        return self.form_class(
            repository=self.manager.repository, session_data=self.session_data
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.get_page_context(context, **kwargs)
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.form_class(
            self.request.POST,
            repository=self.manager.repository,
            session_data=self.session_data,
        )
        if form.is_valid():
            return self.form_valid(form)
        logger.error(f"Form errors: {form.errors}")
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
        return self.form_class(
            repository=self.manager.repository,
            initial=initial,
            session_data=self.session_data,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Update"
        return context


class MontrekDeleteView(
    MontrekPermissionRequiredMixin,
    ReturnToSenderMixin,
    TemplateView,
    MontrekViewMixin,
    MontrekPageViewMixin,
):
    manager_class = MontrekManagerNotImplemented
    success_url = "under_construction"
    do_return_to_referer: bool = True
    template_name = "montrek_delete.html"

    def post(self, request, *args, **kwargs):
        if "action" in request.POST and request.POST["action"] == "Delete":
            self.manager.delete_object(pk=self.kwargs["pk"])
        return HttpResponseRedirect(self.get_success_url())


class MontrekRestApiView(MontrekApiViewMixin, MontrekViewMixin):
    manager_class = MontrekManagerNotImplemented

    def _is_rest(self, request) -> bool:
        return True

    def get(self, request, *args, **kwargs):
        query = self.manager.to_json()
        serializer = MontrekSerializer(query, many=True, manager=self.manager)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def view_dependent_session_data(
        self, session_data: SessionDataType
    ) -> SessionDataType:
        table_meta_session_data = TableMetaSessionData(self.request)
        return table_meta_session_data.update_session_data(session_data)


class MontrekRedirectView(MontrekViewMixin, RedirectView):
    manager_class = MontrekManagerNotImplemented

    def get_redirect_url(self, *args, **kwargs) -> str:
        raise NotImplementedError("Please implement this method in your subclass!")


class MontrekDownloadView(MontrekViewMixin, View):
    manager_class = MontrekManagerNotImplemented

    def get(self, request, *args, **kwargs) -> HttpResponse:
        response = self.manager.download()
        filename = self.manager.get_filename()
        content_type = get_content_type(filename)
        response["Content-Type"] = content_type
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        self.show_messages()
        return response
