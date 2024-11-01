from typing import TextIO
from django.shortcuts import redirect
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import FileResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from file_upload.forms import FieldMapCreateForm, UploadFileForm
from file_upload.managers.file_upload_manager import (
    FileUploadManagerABC,
)
from baseclasses.views import (
    MontrekCreateView,
    MontrekTemplateView,
    MontrekListView,
    MontrekUpdateView,
)
from file_upload.managers.file_upload_registry_manager import FileUploadRegistryManager
from baseclasses.managers.montrek_manager import MontrekManagerNotImplemented
from file_upload.managers.field_map_manager import FieldMapManagerABC
from file_upload.pages import FileUploadPage

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
            if not self._check_file_type(request.FILES["file"], form):
                return self.render_to_response(self.get_context_data())
            self.file_upload_manager = self.file_upload_manager_class(
                request.FILES["file"],
                session_data=self.session_data,
                upload_form=form,
                request=request,
                **self.kwargs,
            )
            result = self.file_upload_manager.upload_and_process()
            if result:
                messages.info(request, self.file_upload_manager.processor.message)
            else:
                messages.error(request, self.file_upload_manager.processor.message)
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
    related_manager_class = MontrekManagerNotImplemented

    def get_form(self, form_class=None):
        return self.form_class(
            repository=self.manager.repository,
            field_map_manager=self.manager_class(self.session_data),
            related_manager=self.related_manager_class(),
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.form_class(
            self.request.POST,
            repository=self.manager.repository,
            field_map_manager=self.manager_class(self.session_data),
            related_manager=self.related_manager_class(),
        )
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)


class MontrekFieldMapUpdateView(MontrekUpdateView):
    manager_class = FieldMapManagerABC
    success_url = "under_construction"
    form_class = FieldMapCreateForm
    related_manager_class = MontrekManagerNotImplemented

    def get_form(self, form_class=None):
        initial = self.manager.get_object_from_pk_as_dict(self.kwargs["pk"])

        return self.form_class(
            repository=self.manager.repository,
            field_map_manager=self.manager_class(self.session_data),
            related_manager=self.related_manager_class(),
            initial=initial,
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.form_class(
            self.request.POST,
            repository=self.manager.repository,
            field_map_manager=self.manager_class(self.session_data),
            related_manager=self.related_manager_class(),
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
