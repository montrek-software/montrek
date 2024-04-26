from typing import TextIO
from django.shortcuts import redirect
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import FileResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from file_upload.forms import FieldMapCreateForm, UploadFileForm
from file_upload.managers.file_upload_manager import FileUploadManager
from file_upload.managers.file_upload_manager import FileUploadProcessorProtocol
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from baseclasses.views import MontrekCreateView, MontrekTemplateView, MontrekListView
from baseclasses.dataclasses.table_elements import (
    DateTableElement,
    LinkTableElement,
    StringTableElement,
)
from file_upload.repositories.field_map_repository import FieldMapRepository
from baseclasses.repositories.montrek_repository import MontrekRepository
from file_upload.managers.field_map_manager import FieldMapManager

# Create your views here.


class NotDefinedFileUploadProcessor:
    message = "File upload processor not defined"

    def process(self, file: TextIO):
        raise NotImplementedError(self.message)

    def pre_check(self, file: TextIO):
        raise NotImplementedError(self.message)

    def post_check(self, file: TextIO):
        raise NotImplementedError(self.message)


@method_decorator(login_required, name="dispatch")
class MontrekUploadFileView(MontrekTemplateView):
    manager_class = FileUploadManager
    template_name = "upload_form.html"
    file_upload_processor_class: type[
        FileUploadProcessorProtocol
    ] = NotDefinedFileUploadProcessor
    accept = ""

    def get_template_context(self, **kwargs):
        return {"form": UploadFileForm(self.accept)}

    def post(self, request, *args, **kwargs):
        form = UploadFileForm(self.accept, request.POST, request.FILES)
        if form.is_valid():
            if not self._check_file_type(request.FILES["file"], form):
                return self.render_to_response(self.get_context_data())
            # TODO: Remodel with self.manager
            file_upload_manager = FileUploadManager(
                self.file_upload_processor_class,
                request.FILES["file"],
                session_data=self.session_data,
                **self.kwargs,
            )
            result = file_upload_manager.upload_and_process()
            if result:
                messages.info(request, file_upload_manager.processor.message)
            else:
                messages.error(request, file_upload_manager.processor.message)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        raise NotImplementedError("get_success_url not implemented")

    def _check_file_type(self, file: TextIO, form: forms.Form) -> bool:
        expected_file_type = form.fields["file"].widget.attrs["accept"].upper()
        if "." + file.name.split(".")[-1].upper() != expected_file_type:
            messages.error(
                self.request,
                f"File type {file.name.split('.')[-1].upper()} not allowed",
            )
            return False
        return True


class MontrekDownloadFileView(MontrekTemplateView):
    repository = FileUploadRegistryRepository

    def get(self, request, *args, **kwargs):
        upload_file = self.repository_object.get_file_from_registry(
            self.kwargs["pk"], self.request
        )
        if upload_file is None:
            return redirect(request.META.get("HTTP_REFERER"))
        return FileResponse(upload_file, as_attachment=True)


class MontrekFieldMapCreateView(MontrekCreateView):
    manager_class = FieldMapManager
    success_url = "under_construction"
    form_class = FieldMapCreateForm
    field_map_manager_class = FieldMapManager
    # TODO: Change to manager
    related_repository_class = MontrekRepository

    def get_form(self, form_class=None):
        return self.form_class(
            repository=self.manager.repository,
            field_map_manager=self.field_map_manager_class(self.session_data),
            related_repository=self.related_repository_class(),
        )

    def post(self, request, *args, **kwargs):
        form = self.form_class(
            self.request.POST,
            repository=self.manager.repository,
            field_map_manager=self.field_map_manager_class(self.session_data),
            related_repository=self.related_repository_class(),
        )
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class MontrekFieldMapListView(MontrekListView):
    manager_class = FieldMapManager
    tab = "tab_field_map_list"
    title = "Field Map Overview"

    @property
    def elements(self) -> list:
        return [
            StringTableElement(name="Source Field", attr="source_field"),
            StringTableElement(name="Database Field", attr="database_field"),
            StringTableElement(name="Function Name", attr="function_name"),
            StringTableElement(name="Function Parameters", attr="function_parameters"),
            StringTableElement(
                name="Comment", attr="field_map_static_satellite_comment"
            ),
        ]

    success_url = "under_construction"


class MontrekUploadView(MontrekListView):
    title = "Uploads"
    tab = "tab_uploads"

    @property
    def elements(self) -> tuple:
        return (
            StringTableElement(name="File Name", attr="file_name"),
            StringTableElement(name="Upload Status", attr="upload_status"),
            StringTableElement(name="Upload Message", attr="upload_message"),
            DateTableElement(name="Upload Date", attr="created_at"),
            LinkTableElement(
                name="File",
                url="montrek_download_file",
                kwargs={"pk": "id"},
                icon="download",
                hover_text="Download",
            ),
        )
