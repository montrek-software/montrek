import logging
import os
from pathlib import Path

from django.contrib.auth.decorators import login_required

from baseclasses.forms import MontrekCreateForm
from baseclasses.sanitizer import HtmlSanitizer
from baseclasses.views import (
    MontrekApiViewMixin,
    MontrekPermissionRequiredMixin,
    MontrekTemplateView,
    MontrekViewMixin,
    ToPdfMixin,
)
from django.conf import settings
from django.forms import ValidationError
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.decorators.http import require_safe
from info.managers.download_registry_storage_managers import (
    DownloadRegistryStorageManager,
)
from info.models.download_registry_sat_models import DOWNLOAD_TYPES
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.mixins.view_form_mixin import ViewFormMixin
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)

# Create your views here.


@require_safe
@login_required
def download_reporting_file_view(request, file_path: str):
    # TODO: Make this view safe by using FileResponse and not rely on paths
    file_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if not os.path.exists(file_path):
        raise Http404
    with open(file_path, "rb") as file:
        response = HttpResponse(file.read(), content_type="application/octet-stream")
        response["Content-Disposition"] = (
            f"attachment; filename={os.path.basename(file_path)}"
        )
        os.remove(file_path)
        download_registry_manager = DownloadRegistryStorageManager(
            {"user_id": request.user.id}
        )
        ext = Path(file_path).suffix.lstrip(".").lower()
        download_registry_manager.store_in_download_registry(
            os.path.basename(file_path), DOWNLOAD_TYPES(ext)
        )
        return response


class MontrekReportView(
    MontrekTemplateView, ToPdfMixin, MontrekApiViewMixin, ViewFormMixin
):
    manager_class = MontrekReportManager
    template_name = "montrek_report.html"
    loading_template_name = "partials/montrek_report_loading.html"
    display_template_name = "partials/montrek_report_display.html"

    def get_template_context(self, load=False) -> dict:
        if load:
            return {
                "report": self.manager.to_html(),
                "report_form": self.report_form.to_html(),
            }
        return {
            "report_form": self.report_form.to_html(),
        }

    def get(self, request, *args, **kwargs):
        self.get_form(request)
        if self.request.GET.get("gen_pdf") == "true":
            return self.list_to_pdf()
        if self.request.GET.get("send_mail") == "true":
            report_manager = LatexReportManager(self.manager)
            pdf_path = report_manager.compile_report()
            return self.manager.prepare_mail(pdf_path)
        if self._is_rest(request):
            return self.list_to_rest_api()
        if request.headers.get("HX-Request"):
            if request.GET.get("state") == "loading":
                # This is the data request - return the content with data
                context = self.get_template_context(load=True)
                return render(request, self.display_template_name, context)
            # For HTMX requests where state is not "loading", return the loading template
            return render(request, self.loading_template_name)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.post_form(request)

    @property
    def title(self):
        return self.manager.document_title

    def list_to_rest_api(self):
        data = self.manager.to_json()
        return Response(data, status=status.HTTP_200_OK)


class MontrekReportFieldEditView(
    MontrekPermissionRequiredMixin, View, MontrekViewMixin
):
    form_class = MontrekCreateForm
    html_sanitizer = HtmlSanitizer()

    def get(self, request, *args, **kwargs):
        obj = self.manager.get_object_from_pk(self.session_data["pk"])
        mode = request.GET.get("mode")
        field = request.GET.get("field")
        object_content = getattr(obj, field)
        object_content = self.html_sanitizer.clean_html(object_content)
        # Determine which mode we're in based on the requested action
        if mode == "edit":
            # Return just the edit form partial
            form = self.form_class(
                repository=self.manager.repository,
                initial={field: object_content},
            )
            formfield = form[field]
            return render(
                request,
                "partials/edit_field.html",
                {
                    "object_content": object_content,
                    "display_url": self.session_data["request_path"],
                    "field": formfield,
                },
            )
        return HttpResponseRedirect("")

    def post(self, request, *args, **kwargs):
        edit_data = self.manager.get_object_from_pk_as_dict(self.session_data["pk"])
        form = self.form_class(self.request.POST, repository=self.manager.repository)
        action = request.POST.get("action")
        field_name = request.POST.get("field")
        if action == "cancel":
            org_field_content = self.html_sanitizer.display_text_as_html(
                edit_data[field_name]
            )
            return render(
                request,
                "partials/display_field.html",
                {
                    "object_content": org_field_content.split("\n"),
                    "edit_url": self.session_data["request_path"],
                    "field": field_name,
                },
            )

        form = self.form_class(self.request.POST, repository=self.manager.repository)
        try:
            # This will validate just the particular field
            field_value = form.fields[field_name].clean(request.POST.get(field_name))
            field_value = HtmlSanitizer().clean_html(str(field_value))
            form.cleaned_data = {field_name: field_value}
            return self.form_valid(form, edit_data, request, field_name)
        except ValidationError as e:
            # Add the error to the form's errors dictionary
            form._errors = {field_name: form.error_class(e.messages)}
            return self.form_invalid(form, edit_data, request, field_name)

    def form_valid(self, form, edit_data: dict, request, field):
        edit_data[field] = form.cleaned_data[field]
        self.manager.repository.create_by_dict(edit_data)
        return render(
            request,
            "partials/display_field.html",
            {
                "object_content": edit_data[field].split("\n"),
                "edit_url": self.session_data["request_path"],
                "field": field,
            },
        )

    def form_invalid(self, form, edit_data, request, field):
        error_message = "\n".join(
            [f"{k}: {', '.join(v)}" for k, v in form.errors.items()]
        )
        formfield = form[field]
        return render(
            request,
            "partials/edit_field.html",
            {
                "object_content": edit_data[field],
                "display_url": self.session_data["request_path"],
                "field": formfield,
                "error_message": error_message,
            },
        )
