import logging
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import urlparse
from django.forms import Form

from django.template.response import TemplateResponse

from baseclasses.views import (
    MontrekApiViewMixin,
    MontrekCreateView,
    MontrekListView,
    MontrekRedirectView,
    MontrekTemplateView,
    MontrekUpdateView,
)
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import resolve, reverse
from file_upload.forms import FieldMapCreateForm, UploadFileForm
from file_upload.managers.field_map_manager import FieldMapManagerABC
from file_upload.managers.file_upload_manager import FileUploadManagerABC
from file_upload.managers.file_upload_registry_manager import (
    FileUploadRegistryManager,
    FileUploadRegistryManagerABC,
)
from file_upload.pages import FileUploadPage
from info.managers.download_registry_storage_managers import (
    DownloadRegistryStorageManager,
)
from info.models.download_registry_sat_models import DownloadType

from montrek.celery_app import app as celery_app
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)
# Create your views here.


NO_FILE_ATTACHED_MESSAGE = "No file attached"


class MontrekUploadFileView(MontrekApiViewMixin, MontrekTemplateView):
    """Upload a file through the browser form or, opt-in, through the REST API.

    Set ``do_rest_upload`` to also accept a multipart POST carrying a JWT
    (``?gen_rest_api=true``, see MontrekApiViewMixin). The REST path runs the
    very same form, permission check and pipeline as the browser path; only the
    responses differ - JSON instead of messages plus a redirect.
    """

    template_name = "upload_form.html"
    file_upload_manager_class = FileUploadManagerABC
    accept = ""
    upload_form_class = UploadFileForm
    # Opt-in per view: an upload endpoint writes data, so it is only reachable
    # for API clients where the view explicitly says so.
    do_rest_upload = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_upload_manager = None

    @classmethod
    def is_rest_request(cls, request) -> bool:
        return cls.do_rest_upload and super().is_rest_request(request)

    def dispatch(self, request, *args, **kwargs):
        # The browser path used to be guarded by a login_required decorator.
        # That cannot stay a decorator: it would run before DRF authenticates
        # and bounce every token client to the login page.
        if not self.is_rest_request(request) and not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)

    def get_template_context(self, **kwargs):
        return {"upload_form": self.upload_form_class(self.accept)}

    def post(self, request, *args, **kwargs):
        form = self.get_post_form(request)
        if form.is_valid():
            return self.form_valid(form, request)
        return self.form_invalid_response(form)

    def form_valid(
        self, form, request
    ) -> HttpResponseRedirect | TemplateResponse | Response:
        logger.debug("Start file upload process")
        file = self.get_file(form)
        file_type_error = self.get_file_type_error(file)
        if file_type_error is not None:
            return self.file_type_error_response(file_type_error)
        self.file_upload_manager = self.file_upload_manager_class(
            session_data=self.session_data,
        )
        self.file_upload_manager.set_pipeline_data(self.get_pipeline_data(form))
        logger.debug("file_upload_manager: %s", self.file_upload_manager)
        result = self.file_upload_manager.upload_and_process(file)
        logger.debug("End file upload process")
        if self._is_rest(request):
            return self.upload_rest_response(result)
        if result:
            messages.info(request, self.file_upload_manager.message)
        else:
            messages.error(request, self.file_upload_manager.message)
        return HttpResponseRedirect(self.get_success_url())

    # ---- responses ----

    def form_invalid_response(self, form: Form) -> TemplateResponse | Response:
        if self._is_rest(self.request):
            return Response(
                {"detail": "Invalid upload request.", "errors": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self.render_to_response(self.get_context_data())

    def file_type_error_response(self, error: str) -> TemplateResponse | Response:
        if self._is_rest(self.request):
            return Response(
                {"detail": error},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )
        messages.error(self.request, error)
        return self.render_to_response(self.get_context_data())

    def upload_rest_response(self, result: bool) -> Response:
        """Report the registry entry the caller has to poll for the outcome.

        Processing usually runs on a Celery worker, so a successful call means
        "accepted", not "imported" - the caller follows ``registry_id`` on the
        upload registry endpoint to learn how it ended.
        """
        manager = self.file_upload_manager
        payload = {
            "registry_id": self.session_data.get(manager.registry_session_key),
            "celery_task_id": self.get_registry_value("celery_task_id"),
            "status": self.get_registry_value(manager.status_field_name),
            "message": manager.message,
        }
        if manager.do_process_async:
            return Response(payload, status=status.HTTP_202_ACCEPTED)
        if result:
            return Response(payload, status=status.HTTP_200_OK)
        return Response(payload, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def get_registry_value(self, field_name: str) -> Any:
        registry = self.file_upload_manager.get_registry()
        return getattr(registry, field_name, None)

    # ---- hooks ----

    def get_success_url(self):
        raise NotImplementedError("get_success_url not implemented")

    def get_pipeline_data(self, form: Form) -> dict:
        """Return what the processor needs from the validated form.

        Override to hand the processor the user's choices instead of letting it
        resolve this view from the request path. Must be JSON serializable — it
        travels to the Celery worker.
        """
        return {}

    def get_file(self, form: Form) -> str:
        return form.cleaned_data["file"]

    def get_file_type_error(self, file: TextIO | None) -> str | None:
        """Return why the file is not acceptable, or None if it is."""
        if file is None:
            return NO_FILE_ATTACHED_MESSAGE
        expected_file_types = [e.lstrip(".").upper() for e in self.accept.split(",")]
        actual_file_type = file.name.split(".")[-1].upper()
        if actual_file_type not in expected_file_types:
            return f"File type {actual_file_type} not allowed"
        return None

    def get_post_form(self, request):
        return self.upload_form_class(self.accept, request.POST, request.FILES)


class MontrekDownloadFileBaseView(MontrekTemplateView):
    manager_class = FileUploadRegistryManager
    page_class = FileUploadPage
    get_file_method = ""

    def get(self, request, *args, **kwargs):
        upload_file = getattr(self.manager.repository, self.get_file_method)(
            self.kwargs["pk"], self.request
        )
        if upload_file is None:
            messages.info(request, "No download file available!")
            return redirect(request.META.get("HTTP_REFERER"))
        ext = Path(upload_file.name).suffix.lstrip(".").lower()
        DownloadRegistryStorageManager(self.session_data).store_in_download_registry(
            self.manager.document_name, DownloadType(ext)
        )
        return FileResponse(upload_file, as_attachment=True)

    def get_template_context(self, **kwargs):
        return {}


class MontrekDownloadFileView(MontrekDownloadFileBaseView):
    get_file_method = "get_upload_file_from_registry"


class MontrekDownloadLogFileView(MontrekDownloadFileBaseView):
    get_file_method = "get_log_file_from_registry"


class MontrekFieldMapCreateView(MontrekCreateView):
    manager_class = FieldMapManagerABC
    success_url = "under_construction"
    form_class = FieldMapCreateForm

    def get_form(self, form_class=None):
        return self.form_class(
            repository=self.manager.repository,
            field_map_manager=self.manager_class(self.session_data),
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.form_class(
            self.request.POST,
            repository=self.manager.repository,
            field_map_manager=self.manager_class(self.session_data),
        )
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class MontrekFieldMapUpdateView(MontrekUpdateView):
    manager_class = FieldMapManagerABC
    success_url = "under_construction"
    form_class = FieldMapCreateForm

    def get_form(self, form_class=None):
        initial = self.manager.get_object_from_pk_as_dict(self.kwargs["pk"])

        return self.form_class(
            repository=self.manager.repository,
            field_map_manager=self.manager_class(self.session_data),
            initial=initial,
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.form_class(
            self.request.POST,
            repository=self.manager.repository,
            field_map_manager=self.manager_class(self.session_data),
        )
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class MontrekFieldMapListView(MontrekListView):
    manager_class = FieldMapManagerABC
    tab = "tab_field_map_list"
    title = "Field Map Overview"

    success_url = "under_construction"
    do_simple_file_upload = True


class FileUploadRegistryView(MontrekListView):
    manager_class = FileUploadRegistryManager
    title = "Uploads"
    tab = "tab_uploads"
    page_class = FileUploadPage


# TODO: Remove after refactor
class MontrekUploadView(FileUploadRegistryView):
    pass


class RevokeFileUploadTask(MontrekRedirectView):
    @property
    def manager_class(self) -> type[FileUploadRegistryManagerABC]:
        previous_url = self.get_previous_url()
        previous_match = resolve(urlparse(previous_url).path)
        try:
            view_class = previous_match.func.view_class
            return view_class.manager_class
        except AttributeError:
            return FileUploadRegistryManager

    def get_redirect_url(self, *args, **kwargs) -> str:
        task_id = self.session_data.get("task_id")
        previous_url = self.get_previous_url()
        success = True
        registry = None

        try:
            celery_app.control.revoke(task_id, terminate=True)
            messages.info(self.request, f"Task {task_id} has been revoked.")
        except Exception as exc:
            messages.error(self.request, str(exc))
            success = False

        repo = self.manager.repository
        if success:
            registry = repo.receive().filter(celery_task_id=task_id).first()
            if registry is None:
                messages.error(self.request, f"Task {task_id} not found in registry.")
                success = False

        if success:
            data = repo.object_to_dict(registry)
            data.update(
                {
                    "upload_status": "revoked",
                    "upload_message": "Task has been revoked",
                }
            )
            repo.create_by_dict(data)

        return previous_url

    def get_previous_url(self):
        return self.request.META.get("HTTP_REFERER", reverse("home"))
