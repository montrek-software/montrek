import os

from django.conf import settings
from django.forms import Form
from django.template import Context, Template


class MontrekReportForm(Form):
    form_template: str | None = None

    def to_html(self) -> str:
        context = Context({"form": self})
        template = Template(self.read_template())
        rendered_template = template.render(context)
        return f"""
    <form method="post">
    {{% csrf_token %}}
    {rendered_template}
    <button type="submit">Submit</button>
    </form>
            """

    def read_template(self) -> str:
        if not self.form_template:
            raise NotImplementedError("MontrekReportForm needs template attribute")
        template_path = self._get_template_path()
        with open(template_path, "r") as file:
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
        raise FileNotFoundError(f"Template {self.form_template} not found")


class NoMontrekReportForm(MontrekReportForm):
    def to_html(self) -> str:
        return ""
