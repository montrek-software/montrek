import os
from datetime import date

from django.conf import settings
from django.forms import DateField, DateInput, Form
from django.template import Context, Template, loader


class MontrekReportForm(Form):
    form_template: str | None = None

    def __init__(self, *args, **kwargs):
        self.session_data = kwargs.pop("session_data", {})
        super().__init__(*args, **kwargs)

    def to_html(self, request=None) -> str:
        """Render the form. The request is needed for the CSRF token of the
        surrounding form tag - without it the POST is rejected."""
        inner = Template(self.read_template()).render(Context({"form": self}))
        wrapper = loader.get_template("report_form_templates/report_form_base.html")
        return wrapper.render({"inner": inner}, request=request)

    def read_template(self) -> str:
        if not self.form_template:
            raise NotImplementedError("MontrekReportForm needs template attribute")
        template_path = self._get_template_path()
        with open(template_path, encoding="utf-8") as file:
            return file.read()

    def _get_template_path(self) -> str:
        for template_dir in settings.TEMPLATES[0]["DIRS"]:
            potential_path = os.path.join(
                settings.BASE_DIR,
                template_dir,
                "report_form_templates",
                str(self.form_template),
            )
            if os.path.exists(potential_path):
                return potential_path
        raise FileNotFoundError(
            f"Template templates/report_form_templates/{self.form_template} not found"
        )


class NoMontrekReportForm(MontrekReportForm):
    def to_html(self, request=None) -> str:
        return ""


class ReportDateReportForm(MontrekReportForm):
    form_template = "report_date_report_form.html"
    report_date = DateField(
        widget=DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        input_formats=["%Y-%m-%d"],
        initial=date.today,
    )
