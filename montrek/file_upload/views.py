from typing import TextIO
from django.shortcuts import redirect
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import FileResponse
from file_upload.forms import UploadFileForm
from file_upload.managers.file_upload_manager import FileUploadManager
from file_upload.managers.file_upload_manager import FileUploadProcessorProtocol
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from baseclasses.views import MontrekTemplateView

# Create your views here.


class NotDefinedFileUploadProcessor:
    message = "File upload processor not defined"

    def process(self, file: TextIO):
        raise NotImplementedError(self.message)

    def pre_check(self, file: TextIO):
        raise NotImplementedError(self.message)

    def post_check(self, file: TextIO):
        raise NotImplementedError(self.message)


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
                messages.success(request, file_upload_manager.processor.message)
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
