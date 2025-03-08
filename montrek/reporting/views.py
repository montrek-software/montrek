import os

from baseclasses.views import (
    MontrekPermissionRequiredMixin,
    MontrekTemplateView,
    MontrekViewMixin,
    ToPdfMixin,
)
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views import View

from reporting.managers.latex_report_manager import LatexReportManager
from reporting.managers.montrek_report_manager import MontrekReportManager

# Create your views here.


def download_reporting_file_view(request, file_path: str):
    file_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if not os.path.exists(file_path):
        raise Http404
    with open(file_path, "rb") as file:
        response = HttpResponse(file.read(), content_type="application/octet-stream")
        response[
            "Content-Disposition"
        ] = f"attachment; filename={os.path.basename(file_path)}"
        os.remove(file_path)
        return response


class MontrekReportView(MontrekTemplateView, ToPdfMixin):
    manager_class = MontrekReportManager
    template_name = "montrek_report.html"

    def get_template_context(self) -> dict:
        return {"report": self.manager.to_html()}

    def get(self, request, *args, **kwargs):
        if self.request.GET.get("gen_pdf") == "true":
            return self.list_to_pdf()
        if self.request.GET.get("send_mail") == "true":
            report_manager = LatexReportManager(self.manager)
            pdf_path = report_manager.compile_report()
            return self.manager.prepare_mail(pdf_path)
        return super().get(request, *args, **kwargs)

    @property
    def title(self):
        return self.manager.document_title


class MontrekReportFieldEditView(
    MontrekPermissionRequiredMixin, View, MontrekViewMixin
):
    def get(self, request, *args, **kwargs):
        obj = self.manager.get_object_from_pk(self.session_data["pk"])
        mode = request.GET.get("mode")
        field = request.GET.get("field")
        object_content = getattr(obj, field)
        # Determine which mode we're in based on the requested action
        if mode == "edit":
            # Return just the edit form partial
            return render(
                request,
                "partials/edit_field.html",
                {
                    "object_content": object_content,
                    "display_url": self.session_data["request_path"],
                    "field": field,
                },
            )
        elif mode == "display":
            # Return just the display partial
            return render(
                request,
                "partials/display_field.html",
                {"object_content": object_content},
            )
        else:
            return HttpResponseRedirect("")

    def post(self, request, *args, **kwargs):
        edit_data = self.manager.get_object_from_pk_as_dict(self.session_data["pk"])

        # Update the model with the submitted content
        field_content = request.POST.get("content")
        field = request.POST.get("field")
        edit_data.update({field: field_content})
        self.manager.repository.create_by_dict(edit_data)

        # Return the updated display partial
        return render(
            request, "partials/display_field.html", {"object_content": field_content}
        )
