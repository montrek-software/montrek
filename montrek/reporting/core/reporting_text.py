import tempfile
import os
from urllib.parse import urlparse

import markdown
import requests
from django.conf import settings
from django.template import Context, Template

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
        if not text:
            text = ""
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

    def to_json(self) -> dict[str, str]:
        return {self.__class__.__name__.lower(): self.text}


class ReportingParagraph(ReportingText):
    def to_latex(self) -> str:
        text = super().to_latex()
        return f"\\begin{{justify}}{text}\\end{{justify}}"

    def to_html(self) -> str:
        return f"<p>{self.text}</p>"


class ReportingEditableText(ReportingParagraph):
    def __init__(
        self,
        obj: HubValueDate,
        field: str,
        edit_url: str,
        header: str = "",
    ):
        text = getattr(obj, field)
        if not text:
            text = ""

        super().__init__(text)
        self.edit_url = edit_url
        self.header = header
        self.field = field

    def to_html(self) -> str:
        return Template(
            f"""<div class="container-fluid">
        <div class="row">
         <div class="col-lg-12" style="padding:0"><h2>{self.header}</h2></div>
         <div id="field-content-container-{self.field}">
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

    def to_latex(self) -> str:
        if self.header != "":
            latex_str = ReportingHeader2(self.header).to_latex()
        else:
            latex_str = ""
        latex_str += super().to_latex()
        return latex_str


class ReportingHeader1:
    def __init__(self, text: str):
        self.text = text

    def to_html(self) -> str:
        return f"<h1>{self.text}</h1>"

    def to_latex(self) -> str:
        return f"\\section*{{{self.text}}}"

    def to_json(self) -> dict[str, str]:
        return {"reporting_header_1": self.text}


class ReportingHeader2:
    def __init__(self, text: str):
        self.text = text

    def to_html(self) -> str:
        return f"<h2>{self.text}</h2>"

    def to_latex(self) -> str:
        return f"\\subsection*{{{self.text}}}"

    def to_json(self) -> dict[str, str]:
        return {"reporting_header_2": self.text}


class Vspace:
    def __init__(self, space: int):
        self.space = space

    def to_latex(self) -> str:
        return f"\\vspace{{{self.space}mm}}"

    def to_html(self) -> str:
        return f'<div style="height:{self.space}mm;"></div>'

    def to_json(self) -> dict[str, int]:
        return {"vspace": self.space}


class NewPage:
    def to_latex(self) -> str:
        return "\\newpage"

    def to_html(self) -> str:
        return "<div style='page-break-after: always; height:15mm;'><hr></div>"

    def to_json(self) -> dict[str, bool]:
        return {"new_page": True}


class ReportingImage:
    def __init__(self, image_path: str, width: float = 1.0):
        self.image_path = image_path
        self.width = width

    def to_latex(self) -> str:
        try:
            urlparse(self.image_path)
            is_url = self.image_path.startswith("http")
        except ValueError:
            is_url = False
        if not is_url:
            if not os.path.exists(self.image_path):
                return ""
            return self._return_string(self.image_path)
        response = requests.get(self.image_path)
        if response.status_code != 200:
            image_path = HtmlLatexConverter.convert(self.image_path)
            return f"Image not found: {image_path}"
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix="." + self.image_path.split(".")[-1].split("?")[0]
        )
        temp_file.write(response.content)
        temp_file_path = temp_file.name
        temp_file.close()
        value = temp_file_path
        return self._return_string(value)

    def _return_string(self, value) -> str:
        value = HtmlLatexConverter.convert(value)
        return f"\\includegraphics[width={self.width}\\textwidth]{{{value}}}"

    def to_html(self) -> str:
        return f'<div style="text-align: right;"><img src="{self.image_path}" alt="image" style="width:{self.width * 100}%;"></div>'

    def to_json(self) -> dict[str, str]:
        return {"reporting_image": self.image_path}


class ReportingMap:
    def __init__(self, longitude: int, latitude: int, offset: int = 5):
        box_coords = [
            longitude - offset,
            latitude + offset,
            longitude + offset,
            latitude - offset,
        ]
        self.embedded_url = f"https://www.openstreetmap.org/export/embed.html?bbox={box_coords[0]}%2C{box_coords[3]}%2C{box_coords[2]}%2C{box_coords[1]}&layer=mapnik&marker={latitude}%2C{longitude}"

    def to_latex(self) -> str:
        # TODO: Implement LaTeX conversion for iframe
        return ""

    def to_html(self) -> str:
        return f'<iframe src="{self.embedded_url}" style="width: 100%; aspect-ratio: 4/3; height: auto; border:2;" loading="lazy" allowfullscreen></iframe>'

    def to_json(self) -> dict[str, str]:
        return {"reporting_map": self.embedded_url}


class MontrekLogo(ReportingImage):
    def __init__(self, width: float = 1.0):
        super().__init__(
            "http://static1.squarespace.com/static/673bfbe149f99b59e4a41ee7/t/673bfdb41644c858ec83dc7e/1731984820187/montrek_logo_variant.png?format=1500w",
            width=width,
        )


class ClientLogo(ReportingImage):
    def __init__(self, width: float = 1.0):
        super().__init__(
            settings.CLIENT_LOGO_PATH,
            width=width,
        )

    def _return_string(self, value) -> str:
        value = HtmlLatexConverter.convert(value)
        return f"\\includegraphics[height=1cm]{{{value}}}"


class MarkdownReportingElement:
    def __init__(self, markdown_text: str):
        self.markdown_text = markdown_text

    def to_html(self) -> str:
        return markdown.markdown(
            self.markdown_text, extensions=["markdown.extensions.tables"]
        )

    def to_latex(self) -> str:
        html_text = self.to_html()
        converter = HtmlLatexConverter()
        return converter.convert(html_text)

    def to_json(self) -> dict[str, str]:
        return {"markdown_reporting_element": self.markdown_text}
