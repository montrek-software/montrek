import os

from baseclasses.views import MontrekTemplateView, ToPdfMixin
from django.conf import settings
from django.http import Http404, HttpResponse

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
