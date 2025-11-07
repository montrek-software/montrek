import logging
import os
from urllib.parse import urlencode

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
from reporting.forms import MontrekReportForm, NoMontrekReportForm
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.managers.montrek_report_manager import MontrekReportManager
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)

# Create your views here.


@require_safe
def download_reporting_file_view(request, file_path: str):
    file_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if not os.path.exists(file_path):
        raise Http404
    with open(file_path, "rb") as file:
        response = HttpResponse(file.read(), content_type="application/octet-stream")
        response["Content-Disposition"] = (
            f"attachment; filename={os.path.basename(file_path)}"
        )
        os.remove(file_path)
        return response


class MontrekReportView(MontrekTemplateView, ToPdfMixin, MontrekApiViewMixin):
    manager_class = MontrekReportManager
    report_form_class = NoMontrekReportForm
    _report_form: MontrekReportForm | None = None
    template_name = "montrek_report.html"
    loading_template_name = "partials/montrek_report_loading.html"
    display_template_name = "partials/montrek_report_display.html"

    @property
    def report_form(self) -> MontrekReportForm:
        if self._report_form is None:
            self._report_form = self.report_form_class()
        return self._report_form

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
        self._report_form = self.report_form_class(data=request.GET)
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
            else:
                # This is the first HTMX request - return loading template
                return render(request, self.loading_template_name)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.report_form_class(request.POST)
        if form.is_valid():
            # Build query string from cleaned_data
            params = {}
            for k, v in form.cleaned_data.items():
                # Normalize booleans to the strings your GET branch expects
                if isinstance(v, bool):
                    params[k] = "true" if v else "false"
                elif v is not None:
                    params[k] = v

            query = urlencode(params, doseq=True)  # doseq handles lists/multi-selects
            url = request.path
            if query:
                url = f"{url}?{query}"

            return HttpResponseRedirect(url)  # triggers your get()

        # Invalid form: fall back to your invalid handler
        logger.error(f"Form errors: {form.errors}")
        return self.form_invalid(form)

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
        else:
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
                    "object_content": org_field_content,
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
        field_content = self.html_sanitizer.display_text_as_html(edit_data[field])
        self.manager.repository.create_by_dict(edit_data)
        return render(
            request,
            "partials/display_field.html",
            {
                "object_content": field_content,
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
