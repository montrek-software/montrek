import logging
from typing import TextIO
from urllib.parse import urlparse

from baseclasses.views import (
    MontrekCreateView,
    MontrekListView,
    MontrekTemplateView,
    MontrekUpdateView,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import resolve
from django.utils.decorators import method_decorator
from file_upload.forms import FieldMapCreateForm, UploadFileForm
from file_upload.managers.field_map_manager import FieldMapManagerABC
from file_upload.managers.file_upload_manager import FileUploadManagerABC
from file_upload.managers.file_upload_registry_manager import FileUploadRegistryManager
from file_upload.pages import FileUploadPage

logger = logging.getLogger(__name__)
# Create your views here.


@method_decorator(login_required, name="dispatch")
class MontrekUploadFileView(MontrekTemplateView):
    template_name = "upload_form.html"
    file_upload_manager_class = FileUploadManagerABC
    accept = ""
    upload_form_class = UploadFileForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_upload_manager = None

    def get_template_context(self, **kwargs):
        return {"form": self.upload_form_class(self.accept)}

    def post(self, request, *args, **kwargs):
        form = self.get_post_form(request)
        if form.is_valid():
            logger.debug("Start file upload process")
            if not self._check_file_type(request.FILES["file"]):
                return self.render_to_response(self.get_context_data())
            self.file_upload_manager = self.file_upload_manager_class(
                session_data=self.session_data,
            )
            logger.debug("file_upload_manager: %s", self.file_upload_manager)
            result = self.file_upload_manager.upload_and_process(request.FILES["file"])
            if result:
                messages.info(request, self.file_upload_manager.message)
            else:
                messages.error(request, self.file_upload_manager.message)
            logger.debug("End file upload process")
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        raise NotImplementedError("get_success_url not implemented")

    def _check_file_type(self, file: TextIO) -> bool:
        expected_file_types = self.accept.split(",")
        expected_file_types = [e.lstrip(".").upper() for e in expected_file_types]
        actual_file_type = file.name.split(".")[-1].upper()
        if actual_file_type not in expected_file_types:
            messages.error(
                self.request,
                f"File type {actual_file_type} not allowed",
            )
            return False
        return True

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


def revoke_file_upload_task(request, task_id: str):
    """
    Kill a running celery file upload task and update the corresponding
    registry entry.
    """
    previous_url = request.META.get("HTTP_REFERER")
    try:
        celery_app.control.revoke(task_id, terminate=True)
        messages.info(request, f"Task {task_id} has been revoked.")
    except Exception as e:
        messages.error(request, str(e))
    if not previous_url:
        return HttpResponseRedirect("/")
    previous_match = resolve(urlparse(previous_url).path)
    view_class = previous_match.func.view_class
    repository_class = view_class.manager_class.repository_class
    session_data = previous_match.kwargs
    session_data["user_id"] = request.user.id
    registry_repository = repository_class(session_data)
    registry = registry_repository.receive().get(celery_task_id=task_id)
    redirect = HttpResponseRedirect(previous_url)
    if not registry:
        messages.error(request, f"Task {task_id} not found in registry.")
        return redirect
    registry_dict = registry_repository.object_to_dict(registry)
    registry_dict["upload_status"] = "revoked"
    registry_dict["upload_message"] = "Task has been revoked"
    registry_repository.create_by_dict(registry_dict)
    return redirect
