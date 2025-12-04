import os

from django.conf import settings
from django.forms import Form
from django.template import Context, Template, loader


class MontrekReportForm(Form):
    form_template: str | None = None

    def to_html(self) -> str:
        inner = Template(self.read_template()).render(Context({"form": self}))
        wrapper = loader.get_template("report_form_templates/report_form_base.html")
        return wrapper.render({"inner": inner})

    def read_template(self) -> str:
        if not self.form_template:
            raise NotImplementedError("MontrekReportForm needs template attribute")
        template_path = self._get_template_path()
        with open(template_path, "r", encoding="utf-8") as file:
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
    def to_html(self) -> str:
        return ""
