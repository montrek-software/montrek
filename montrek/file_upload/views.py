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
from baseclasses.dataclasses.table_elements import StringTableElement
from baseclasses.dataclasses.view_classes import ActionElement
from file_upload.repositories.field_map_repository import FieldMapRepository
from file_upload.pages import FieldMapPage

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


class MontrekFieldMapCreate(MontrekCreateView):
    repository = FieldMapRepository
    page_class = FieldMapPage
    success_url = "montrek_example_field_map_list"
    form_class = FieldMapCreateForm


class MontrekFieldMapList(MontrekListView):
    repository = FieldMapRepository
    page_class = FieldMapPage
    tab = "tab_field_map_list"
    title = "Field Map Overview"

    @property
    def elements(self) -> list:
        return [
            StringTableElement(name="Source Field", attr="source_field"),
            StringTableElement(name="Database Field", attr="database_field"),
        ]

    @property
    def actions(self) -> tuple:
        action_new_field_map = ActionElement(
            icon="plus",
            link=reverse("montrek_example_field_map_create"),
            action_id="id_new_field_map",
            hover_text="Add new Field Map",
        )
        return (action_new_field_map,)

    success_url = "montrek_example_field_map_list"


class MontrekUploadView(MontrekListView):
    title = "Uploads"
    tab = "tab_uploads"

    @property
    def elements(self) -> tuple:
        return (
            te.StringTableElement(name="File Name", attr="file_name"),
            te.StringTableElement(name="Upload Status", attr="upload_status"),
            te.StringTableElement(name="Upload Message", attr="upload_message"),
            te.DateTableElement(name="Upload Date", attr="created_at"),
            te.LinkTableElement(
                name="File",
                url="montrek_download_file",
                kwargs={"pk": "id"},
                icon="download",
                hover_text="Download",
            ),
        )
