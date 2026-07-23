import logging
import os
from pathlib import Path
from typing import Any, BinaryIO, Protocol

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_safe
from django.views.generic import DetailView, RedirectView, View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from baseclasses.templatetags.base_tags import project_display_name
from file_upload.forms import SimpleUploadFileForm
from file_upload.managers.simple_upload_file_manager import SimpleUploadFileManager
from info.managers.download_registry_storage_managers import (
    DownloadRegistryStorageManager,
)
from info.models.download_registry_sat_models import DownloadType
from reporting.constants import PdfGenMethod
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.managers.weasyprint_pdf_manager import WeasyPrintPdfManager
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.managers.montrek_table_manager import (
    HistoryDataTableManager,
    MontrekDataFrameTableManager,
    MontrekTableManager,
)
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from baseclasses import utils
from baseclasses.dataclasses.montrek_message import MontrekMessageError
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.forms import DateRangeForm, FilterForm, MontrekCreateForm
from baseclasses.managers.montrek_manager import MontrekManagerNotImplemented
from baseclasses.pages import NoPage
from baseclasses.sanitizer import HtmlSanitizer
from baseclasses.serializers import MontrekSerializer
from baseclasses.typing import SessionDataType
from baseclasses.utils import TableMetaSessionData, get_content_type

logger = logging.getLogger(__name__)

# Response header set on a successful inline-field-edit save/cancel; the inline
# editor row (see tables/partials/inline_edit_row.html) reads it to know it may
# remove itself once the re-rendered data row has been swapped in above it.
INLINE_EDIT_DONE_HEADER = "HX-Inline-Edit-Done"


@require_safe
def redirect_home(request):
    redirect_url = settings.HOME_URL
    return redirect(reverse(redirect_url))


def _get_greeting() -> str:
    hour = timezone.localtime().hour
    if hour < 12:
        return "Guten Morgen"
    if hour < 18:
        return "Guten Tag"
    return "Guten Abend"


@require_safe
def home(request):
    project_name = project_display_name()
    first_name = getattr(request.user, "first_name", "")
    return render(
        request,
        "home.html",
        context={
            "project_name": project_name,
            "greeting": _get_greeting(),
            "first_name": first_name,
            "today": timezone.localdate(),
        },
    )


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
            elif message.message_type == "warning":
                messages.warning(self.request, message.message)
            else:
                messages.success(self.request, message.message)

    def get_view_queryset(self):
        return self.manager.repository.receive()


class MontrekPermissionRequiredMixin(PermissionRequiredMixin):
    permission_required = []

    def handle_no_permission(self):
        # handled by PermissionErrorMiddleware
        raise PermissionDenied


class ToPdfMixin:
    pdf_gen_method: PdfGenMethod = PdfGenMethod.WEASYPRINT

    def list_to_pdf(self):
        if self.pdf_gen_method == PdfGenMethod.LATEX:
            return self.list_to_pdf_latex()
        return self._list_to_pdf_weasyprint()

    def _list_to_pdf_weasyprint(self):
        """HTML → PDF via WeasyPrint."""
        manager = WeasyPrintPdfManager(self.manager)
        pdf_bytes = manager.generate_pdf()
        if not pdf_bytes:
            self.manager.messages.append(
                MontrekMessageError("PDF generation failed. Please try again.")
            )
        self.show_messages()
        if pdf_bytes:
            DownloadRegistryStorageManager(
                self.session_data
            ).store_in_download_registry(self.manager.document_name, DownloadType.PDF)
            filename = f"{self.manager.document_name}.pdf"
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        previous_url = self.request.META.get("HTTP_REFERER") or self.request.path
        return HttpResponseRedirect(previous_url)

    def list_to_pdf_latex(self):
        """Opt-in LaTeX path: full XeLaTeX typesetting (?gen_pdf=latex)."""
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
    simple_file_upload_permission: list[str] = []

    def get(self, request, *args, **kwargs):
        q = request.GET
        response = None

        if q.get("gen_csv") == "true":
            response = self.list_to_csv()
        elif q.get("gen_excel") == "true":
            response = self.list_to_excel()
        elif q.get("gen_pdf") in ("true", "latex"):
            response = (
                self.list_to_pdf_latex()
                if q.get("gen_pdf") == "latex"
                else self.list_to_pdf()
            )
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
        if not isinstance(
            self.manager, MontrekTableManager | MontrekDataFrameTableManager
        ):
            raise ValueError(
                f"Manager {self.manager.__class__.__name__} must be of type MontrekTableManager or MontrekDataFrameTableManager"
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
        if self.simple_file_upload_permission and not request.user.has_perms(
            self.simple_file_upload_permission
        ):
            raise PermissionDenied
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
    _prefetched_object = None

    @property
    def manager(self):
        if self._manager is None:
            if issubclass(self.manager_class, MontrekDetailsManager):
                self._manager = self.manager_class(
                    self.session_data, object_query=self._prefetched_object
                )
            else:
                self._manager = self.manager_class(self.session_data)
        return self._manager

    def get_queryset(self):
        return self.get_view_queryset()

    def get_object(self, queryset=None):
        if self._prefetched_object is not None:
            return self._prefetched_object
        return super().get_object(queryset)

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
        if request_get.get("gen_pdf") == "latex":
            return self.list_to_pdf_latex()
        if self._is_rest(request):
            return self.list_to_rest_api()
        return super().get(request, *args, **kwargs)

    def _set_hub_value_date_pk(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        # Expose the requested hub pk to the repository so hub-scoped
        # repositories can anchor value date selection to this hub instead of
        # a globally computed date.
        hub_pk = kwargs["pk"]
        self.session_data["hub_pk"] = hub_pk
        # Keep the fetched row so the manager and get_object() can reuse it
        # instead of re-running the (potentially expensive) annotated query.
        self._prefetched_object = (
            self.manager_class.repository_class(dict(self.session_data))
            .receive()
            .get(hub_entity_id=hub_pk)
        )
        hub_value_date_pk = self._prefetched_object.pk
        kwargs["pk"] = hub_value_date_pk
        self.kwargs["pk"] = hub_value_date_pk
        # session_data is cached at this point; the manager expects the
        # hub value date pk, not the hub pk.
        self._session_data["pk"] = hub_value_date_pk
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
    is_compact_form: bool = False
    template_name = "montrek_create.html"
    compact_template_name = "montrek_create_compact.html"
    do_return_to_referer: bool = False
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

    def get_template_names(self):
        if self.is_compact_form:
            return [self.compact_template_name]
        return [self.template_name]

    def get_queryset(self):
        return self.get_view_queryset()

    def form_valid(self, form):
        self.object = self.manager.create_object(data=form.cleaned_data)
        self.show_messages()
        return HttpResponseRedirect(self.get_success_url())

    def get_form(self, form_class=None):
        form = self.form_class(
            repository=self.manager.repository, session_data=self.session_data
        )
        form.set_field_order()
        return form

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
    go_to_details: bool = False

    def _get_initial(self) -> dict:
        return self.manager.get_object_from_pk_as_dict(self.kwargs["pk"])

    def get_form(self, form_class=None):
        return self.form_class(
            repository=self.manager.repository,
            initial=self._get_initial(),
            session_data=self.session_data,
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.form_class(
            self.request.POST,
            repository=self.manager.repository,
            session_data=self.session_data,
            initial=self._get_initial(),
        )
        if form.is_valid():
            return self.form_valid(form)
        logger.error(f"Form errors: {form.errors}")
        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Update"
        return context

    def get_success_url(self):
        """
        Return the post-update redirect target.

        If ``do_return_to_referer`` is enabled, defer to the parent
        implementation so the user is sent back to the referring page.
        Otherwise, return the configured ``success_url`` directly when
        ``go_to_details`` is false, or reverse ``success_url`` with the
        session ``pk`` when redirecting to a details view. If no session
        ``pk`` is available, fall back to reversing ``success_url``
        without kwargs.
        """
        if self.do_return_to_referer:
            return super().get_success_url()
        if not self.go_to_details:
            return reverse(self.success_url)
        object_pk = self.session_data.get("pk")
        if object_pk is not None:
            return reverse(self.success_url, kwargs={"pk": object_pk})
        return reverse(self.success_url)


class MontrekDeleteView(
    MontrekPermissionRequiredMixin,
    ReturnToSenderMixin,
    TemplateView,
    MontrekViewMixin,
    MontrekPageViewMixin,
):
    manager_class = MontrekManagerNotImplemented
    success_url = "under_construction"
    do_return_to_referer: bool = False
    template_name = "montrek_delete.html"

    def post(self, request, *args, **kwargs):
        self.deleted_object = None
        if "action" in request.POST and request.POST["action"] == "Delete":
            self.deleted_object = self.manager.delete_object(pk=self.kwargs["pk"])
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


class MontrekHtmxRowRenderMixin:
    """Answer an HTMX request with a single re-rendered table row.

    Counterpart of table elements that target their own row
    (``hx-target="closest tr"``, ``hx-swap="outerHTML"``, e.g.
    ``HtmxLinkTableElement``): the view re-renders only the affected row via
    ``row_table_manager_class`` instead of reloading the whole page. Configure

    - ``row_table_manager_class``: the ``MontrekTableManager`` of the table
      the row lives in,
    - ``get_row_table_session_data()``: session data for that manager (e.g.
      to swap the ``pk`` for the parent object's), and
    - ``get_row_filter_kwargs()``: how to find the row in the manager's
      full table (defaults to the session ``pk``).

    Set ``hx_trigger_event`` to additionally fire a client-side event so
    other page fragments (summaries, counters) can refresh themselves.
    """

    row_table_manager_class: type[MontrekTableManager] | None = None
    hx_trigger_event: str | None = None
    _row_table_manager: MontrekTableManager | None = None

    @property
    def row_table_manager(self) -> MontrekTableManager:
        if self._row_table_manager is None:
            if self.row_table_manager_class is None:
                raise NotImplementedError(
                    "Assign the table manager of the table containing the row "
                    "to row_table_manager_class"
                )
            self._row_table_manager = self.row_table_manager_class(
                self.get_row_table_session_data()
            )
        return self._row_table_manager

    def get_row_table_session_data(self) -> SessionDataType:
        return self.session_data

    def get_row_filter_kwargs(self) -> dict[str, Any]:
        return {"pk": self.session_data.get("pk")}

    def get_htmx_row_object(self) -> Any | None:
        """Fetch the row this view acts on, or None if it's gone."""
        table_manager = self.row_table_manager
        full_table = table_manager.get_full_table()
        if not hasattr(full_table, "filter"):
            raise TypeError(
                f"{table_manager.__class__.__name__}.get_full_table() must return "
                "a QuerySet to support HTMX row rendering"
            )
        return full_table.filter(**self.get_row_filter_kwargs()).first()

    def render_htmx_row(self) -> HttpResponse | None:
        """Return the re-rendered ``<tr>``, or None if the row is gone."""
        row = self.get_htmx_row_object()
        if row is None:
            return None
        response = HttpResponse(self.row_table_manager.render_single_row(row))
        if self.hx_trigger_event:
            response["HX-Trigger"] = self.hx_trigger_event
        return response

    def htmx_row_response(self) -> HttpResponse:
        """Row response with a full-page-refresh fallback if the row is gone
        (e.g. it dropped out of the filtered table after the action)."""
        response = self.render_htmx_row()
        if response is None:
            response = HttpResponse()
            response["HX-Refresh"] = "true"
        return response


class MontrekHtmxRowActionView(MontrekHtmxRowRenderMixin, MontrekRedirectView):
    """Run a manager method and swap the affected table row in place.

    On HTMX requests the response is just the re-rendered ``<tr>`` (plus an
    optional ``HX-Trigger`` event); without HTMX the view degrades to a
    normal redirect, so ``get_redirect_url`` must still be implemented.
    """

    method: str = ""

    def run_action(self) -> None:
        getattr(self.manager, self.method)()

    def get(self, request, *args, **kwargs):
        self.run_action()
        self.show_messages()
        if request.headers.get("HX-Request"):
            partial = self.render_htmx_row()
            if partial is not None:
                return partial
        return super().get(request, *args, **kwargs)


class MontrekInlineFieldEditView(
    MontrekPermissionRequiredMixin, MontrekHtmxRowRenderMixin, View, MontrekViewMixin
):
    """Edit a single satellite field inline within a table row via HTMX.

    Pair with an ``InlineEditTableElement`` pointing at this view:

    - GET replaces the clicked data row (``hx-swap="outerHTML"``) with two rows: a
      freshly rendered copy of the data row, followed by a full-width editor row
      directly below it containing the field editor and save/cancel buttons,
    - POST with action "save" validates the field, persists it through the
      manager's repository and returns the plain re-rendered data row,
    - POST with action "cancel" returns the unchanged data row.

    Configure ``field_name`` (the repository field to edit) alongside the
    ``MontrekHtmxRowRenderMixin`` attributes. Field label and validation come
    from the repository (``display_field_names``, satellite validators).
    Non-HTMX requests are redirected to ``get_fallback_url()``.

    The editor form uses ``get_edit_row_id()`` as its form prefix, so the
    input is named e.g. ``inline-edit-42-damage_value_comment``. This is
    required for correctness: the whole table lives inside a form (see
    ``tables/base_table.html``) whose values HTMX submits with every non-GET
    request, so when editors are open on several rows at once all their
    textareas are posted together — without the per-row prefix they would
    share one name and ``request.POST.get()`` would return whichever textarea
    comes last in the DOM, silently saving another row's (possibly empty)
    value.
    """

    form_class = MontrekCreateForm
    field_name: str = ""
    template_name = "tables/partials/inline_edit_row.html"

    def get(self, request, *args, **kwargs):
        if not request.headers.get("HX-Request"):
            return HttpResponseRedirect(self.get_fallback_url())
        form = self.form_class(
            repository=self.manager.repository,
            initial=self.get_edit_data(),
            session_data=self.session_data,
            prefix=self.get_edit_row_id(),
        )
        return self.render_edit_row(request, form)

    def post(self, request, *args, **kwargs):
        if not request.headers.get("HX-Request"):
            return HttpResponseRedirect(self.get_fallback_url())
        if request.POST.get("action") == "cancel":
            return self._row_done_response()
        edit_data = self.get_edit_data()
        form = self.form_class(
            request.POST,
            repository=self.manager.repository,
            initial=edit_data,
            session_data=self.session_data,
            prefix=self.get_edit_row_id(),
        )
        try:
            # Read the value under its row-prefixed name (see the prefix note
            # in the class docstring): a bare ``self.field_name`` lookup would
            # pick up a same-named textarea of another open editor row, since
            # the enclosing table form submits every open editor's inputs.
            field_value = form.fields[self.field_name].clean(
                request.POST.get(form.add_prefix(self.field_name))
            )
        except ValidationError as error:
            return self.render_edit_row(
                request,
                form,
                error_message=", ".join(error.messages),
                include_data_row=False,
            )
        edit_data[self.field_name] = field_value
        self.save_field(edit_data)
        self.show_messages()
        return self._row_done_response()

    def _row_done_response(self) -> HttpResponse:
        """The re-rendered data row plus a marker header telling the inline
        editor row (which triggered this request) to remove itself once the
        data row above it has been swapped in — see ``inline_edit_row.html``."""
        response = self.htmx_row_response()
        response[INLINE_EDIT_DONE_HEADER] = "1"
        return response

    def get_edit_data(self) -> dict:
        return self.manager.get_object_from_pk_as_dict(self.session_data["pk"])

    def save_field(self, edit_data: dict) -> None:
        self.manager.repository.create_by_dict(edit_data)

    def get_fallback_url(self) -> str:
        return self.session_data.get("http_referer") or reverse(settings.HOME_URL)

    def get_display_cells(self) -> list:
        row = self.get_htmx_row_object()
        if row is None:
            return []
        return [
            table_element.get_display_field(row)
            for table_element in self.row_table_manager.table_elements
        ]

    def get_edit_row_id(self) -> str:
        return f"inline-edit-{self.session_data['pk']}"

    def render_edit_row(
        self,
        request,
        form,
        error_message: str | None = None,
        include_data_row: bool = True,
    ) -> HttpResponse:
        edit_row_id = self.get_edit_row_id()
        response = render(
            request,
            self.template_name,
            {
                "cells": self.get_display_cells() if include_data_row else [],
                "include_data_row": include_data_row,
                "colspan": len(self.row_table_manager.table_elements),
                "edit_row_id": edit_row_id,
                "field": form[self.field_name],
                "post_url": self.session_data["request_path"],
                "error_message": error_message,
            },
        )
        if not include_data_row:
            # Validation re-render: the buttons normally target the data row
            # above (``previous tr``); retarget so the editor row replaces
            # itself in place and the data row is left untouched.
            response["HX-Retarget"] = f"#{edit_row_id}"
            response["HX-Reswap"] = "outerHTML"
        return response


class MontrekDownloadView(MontrekViewMixin, View):
    manager_class = MontrekManagerNotImplemented

    def get(self, request, *args, **kwargs) -> HttpResponse:
        response = self.manager.download()
        filename = self.manager.get_filename()
        content_type = get_content_type(filename)
        response["Content-Type"] = content_type
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        ext = Path(filename).suffix.lstrip(".").lower()
        DownloadRegistryStorageManager(self.session_data).store_in_download_registry(
            self.manager.document_name, DownloadType(ext)
        )
        self.show_messages()
        return response
