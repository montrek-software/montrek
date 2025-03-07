import tempfile
from urllib.parse import urlparse

import requests
from baseclasses.models import HubValueDate
from reporting.constants import ReportingTextType
from reporting.core.reporting_mixins import ReportingChecksMixin
from reporting.core.reporting_protocols import ReportingElement
from reporting.core.text_converter import HtmlLatexConverter
from reporting.lib.protocols import (
    ReportElementProtocol,
)


class ReportingTextParagraph(ReportingElement, ReportingChecksMixin):
    def __init__(self, text_type: ReportingTextType = ReportingTextType.PLAIN):
        self.text = None
        self.text_type = text_type

    def generate(self, data: str) -> None:
        self.text = data

    def format_latex(self) -> str:
        self._check_for_generating()
        if self.text_type == ReportingTextType.PLAIN:
            return f"{self.text}\n\n"
        return self.text

    def format_html(self) -> str:
        return self._format_to_html()

    def format_mail(self) -> str:
        return self._format_to_html()

    def _format_to_html(self) -> str:
        self._check_for_generating()
        if self.text_type == ReportingTextType.PLAIN:
            return f"<p>{self.text}</p>"
        return self.text


class ReportingText(ReportElementProtocol):
    def __init__(
        self,
        text: str,
        reporting_text_type: ReportingTextType = ReportingTextType.HTML,
    ):
        self.text = text
        self.reporting_text_type = reporting_text_type

    def to_latex(self) -> str:
        match self.reporting_text_type:
            case ReportingTextType.PLAIN:
                text = self.text
            case ReportingTextType.HTML:
                text = HtmlLatexConverter.convert(self.text)
            case _:
                text = f"\\textbf{{\\color{{red}} Unknown Text Type {self.reporting_text_type}"
        return text

    def to_html(self) -> str:
        return self.text


class ReportingParagraph(ReportingText):
    def to_latex(self) -> str:
        text = super().to_latex()
        return f"\\begin{{justify}}{text}\\end{{justify}}"

    def to_html(self) -> str:
        return f"<p>{self.text}</p>"


from django.template import Context, Template


class ReportingEditableText(ReportingText):
    def __init__(
        self,
        obj: HubValueDate,
        field: str,
        edit_url: str = "",
        header: str = "",
    ):
        text = getattr(obj, field)

        super().__init__(text)
        self.edit_url = edit_url
        self.header = header
        self.field = field

    def to_html(self) -> str:
        return Template(
            f"""<div class="container-fluid">
        <div class="row">
         <div class="col-lg-12" style="padding:0"><h2>{self.header}</h2></div>
         <div id="field-content-container">
             {{% include "partials/display_field.html" %}}
         </div>
        </div>
</div>"""
        ).render(
            Context(
                {
                    "object_content": self.text,
                    "edit_url": self.edit_url,
                    "field": self.field,
                }
            )
        )


class ReportingHeader1:
    def __init__(self, text: str):
        self.text = text

    def to_html(self) -> str:
        return f"<h1>{self.text}</h1>"

    def to_latex(self) -> str:
        return f"\\section*{{{self.text}}}"


class ReportingHeader2:
    def __init__(self, text: str):
        self.text = text

    def to_html(self) -> str:
        return f"<h2>{self.text}</h2>"

    def to_latex(self) -> str:
        return f"\\subsection*{{{self.text}}}"


class Vspace:
    def __init__(self, space: int):
        self.space = space

    def to_latex(self) -> str:
        return f"\\vspace{{{self.space}mm}}"

    def to_html(self) -> str:
        return f'<div style="height:{self.space}mm;"></div>'


class NewPage:
    def to_latex(self) -> str:
        return "\\newpage"

    def to_html(self) -> str:
        return "<div style='page-break-after: always; height:15mm;'><hr></div>"


class ReportingImage:
    def __init__(self, image_path: str, width: float = 1.0):
        self.image_path = image_path
        self.width = width

    def to_latex(self) -> str:
        try:
            urlparse(self.image_path)
            is_url = True
        except ValueError:
            is_url = False
        if not is_url:
            return self._return_string(self.image_path)
        response = requests.get(self.image_path)
        if response.status_code != 200:
            return f"Image not found: {self.image_path} &"
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix="." + self.image_path.split(".")[-1].split("?")[0]
        )
        temp_file.write(response.content)
        temp_file_path = temp_file.name
        temp_file.close()
        value = temp_file_path
        return self._return_string(value)

    def _return_string(self, value) -> str:
        return f"\\includegraphics[width={self.width}\\textwidth]{{{value}}}"

    def to_html(self) -> str:
        return f'<div style="text-align: right;"><img src="{self.image_path}" alt="image" style="width:{self.width*100}%;"></div>'


class MontrekLogo(ReportingImage):
    def __init__(self, width: float = 1.0):
        super().__init__(
            "http://static1.squarespace.com/static/673bfbe149f99b59e4a41ee7/t/673bfdb41644c858ec83dc7e/1731984820187/montrek_logo_variant.png?format=1500w",
            width=width,
        )
