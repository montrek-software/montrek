import hashlib
import mistune
import os
from pathlib import Path
from urllib.parse import urlparse

import pypandoc
import requests
from baseclasses.models import HubValueDate
from baseclasses.sanitizer import HtmlSanitizer
from django.conf import settings
from django.template.loader import render_to_string
from reporting.core.text_converter import HtmlLatexConverter

type ContextTypes = dict[str, str | list[str] | int | float | object]


class ReportingElement:
    template_name: str = ""

    def get_context_data(self) -> ContextTypes:
        return {}

    def to_html(self) -> str:
        return render_to_string(
            f"reporting_elements/{self.template_name}.html", self.get_context_data()
        )

    def to_latex(self) -> str:
        html_text = self.to_html()
        return HtmlLatexConverter.convert(html_text)


class ReportingTextParagraph(ReportingElement):
    def __init__(self, text: str):
        self.text = text

    def format_latex(self) -> str:
        return self.text

    def format_html(self) -> str:
        return self._format_to_html()

    def _format_to_html(self) -> str:
        raise NotImplementedError("This needs to be replaced!!")
        return f'<div class="scrollable-600">{self.text}</div>'


class ReportingText(ReportingElement):
    template_name = "text"

    def __init__(
        self,
        text: str,
    ):
        if not text:
            text = ""
        self.text = str(text)

    def to_latex(self) -> str:
        return HtmlLatexConverter.convert(self.text)

    def get_context_data(self) -> ContextTypes:
        return {"text": HtmlSanitizer().display_text_as_html(self.text)}

    def to_json(self) -> dict[str, str]:
        return {self.__class__.__name__.lower(): self.text}


class ReportingParagraph(ReportingText):
    template_name = "paragraph"

    def to_latex(self) -> str:
        text = super().to_latex()
        return f"\\begin{{justify}}{text}\\end{{justify}}"


class ReportingEditableText(ReportingParagraph):
    template_name = "editable_text"

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

    def get_context_data(self) -> ContextTypes:
        return {
            "header": self.header,
            "object_content": self.text.split("\n"),
            "edit_url": self.edit_url,
            "field": self.field,
        }

    def to_latex(self) -> str:
        if self.header != "":
            latex_str = ReportingHeader2(self.header).to_latex()
        else:
            latex_str = ""
        latex_str += super().to_latex()
        return latex_str


class ReportingBold(ReportingText):
    template_name = "bold"

    def to_latex(self) -> str:
        latex = super().to_latex()
        return f"\\textbf{{{latex}}}"


class ReportingItalic(ReportingText):
    template_name = "italic"

    def to_latex(self) -> str:
        latex = super().to_latex()
        return f"\\emph{{{latex}}}"


class ReportingUnderline(ReportingText):
    template_name = "underline"

    def to_latex(self) -> str:
        latex = super().to_latex()
        return f"\\underline{{{latex}}}"


class ReportingStrikethrough(ReportingText):
    template_name = "strikethrough"

    def to_latex(self) -> str:
        latex = super().to_latex()
        return f"\\underline{{{latex}}}"


class ReportingCode(ReportingText):
    template_name = "code"

    def to_latex(self) -> str:
        latex = super().to_latex()
        return f"\\texttt{{{latex}}}"


class ReportingKeyboard(ReportingText):
    template_name = "keyboard"

    def to_latex(self) -> str:
        # approximation
        latex = super().to_latex()
        return f"\\texttt{{{latex}}}"


class ReportingHeader1(ReportingText):
    template_name = "header1"

    def __init__(self, text: str):
        self.text = text

    def to_latex(self) -> str:
        return f"\\section*{{{self.text}}}"

    def to_json(self) -> dict[str, str]:
        return {"reporting_header_1": self.text}


class ReportingHeader2(ReportingText):
    template_name = "header2"

    def __init__(self, text: str):
        self.text = text

    def to_latex(self) -> str:
        return f"\\subsection*{{{self.text}}}"

    def to_json(self) -> dict[str, str]:
        return {"reporting_header_2": self.text}


class Vspace(ReportingElement):
    template_name = "vspace"

    def __init__(self, space: int):
        self.space = space

    def to_latex(self) -> str:
        return f"\\vspace{{{self.space}mm}}"

    def to_json(self) -> ContextTypes:
        return {"vspace": self.space}

    def get_context_data(self) -> ContextTypes:
        return self.to_json()


class NewPage(ReportingElement):
    template_name = "new_page"

    def to_latex(self) -> str:
        return "\\newpage"

    def to_json(self) -> dict[str, bool]:
        return {"new_page": True}


class ReportingImage(ReportingElement):
    template_name = "image"

    def __init__(self, image_path: str, width: float = 1.0):
        self.image_path = image_path
        self.width = width

    def to_latex(self) -> str:
        try:
            parsed = urlparse(self.image_path)
            is_url = parsed.scheme in {"http", "https"}
        except ValueError:
            is_url = False

        if not is_url:
            if not os.path.exists(self.image_path):
                return ""
            return self._return_string(self.image_path)

        # Remote image: download and save to WORKBENCH_PATH
        response = requests.get(self.image_path, timeout=5)
        if response.status_code != 200:
            image_path = HtmlLatexConverter.convert(self.image_path)
            return f"Image not found: {image_path}"

        # Derive a unique filename from the URL (safe and repeatable)
        ext = Path(self.image_path).suffix.split("?")[0] or ".png"
        hash_name = hashlib.sha256(
            self.image_path.encode("utf-8")
        ).hexdigest()  # nosec B324 - weak MD5 hash is justified
        filename = f"{hash_name}{ext}"
        image_path = settings.WORKBENCH_PATH / filename

        # Save the file to WORKBENCH_PATH
        with open(image_path, "wb") as f:
            f.write(response.content)

        return self._return_string(str(image_path))

    def _return_string(self, value) -> str:
        value = HtmlLatexConverter.convert(value)
        return f"\\includegraphics[width={self.width}\\textwidth]{{{value}}}"

    def to_json(self) -> dict[str, str]:
        return {"reporting_image": self.image_path}

    def get_context_data(self) -> ContextTypes:
        return {"reporting_image": self.image_path, "width": self.width * 100}


class ReportingMap(ReportingElement):
    template_name = "map"

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

    def to_json(self) -> dict[str, str]:
        return {"reporting_map": self.embedded_url}

    def get_context_data(self) -> ContextTypes:
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


class MarkdownReportingElement(ReportingElement):
    template_name = "markdown"

    def __init__(self, markdown_text: str):
        self.markdown_text = markdown_text

    def convert_to_html(self) -> str:
        markdown_to_html = mistune.create_markdown(
            escape=False,
            plugins=[
                "strikethrough",
                "table",
                "task_lists",
            ],
        )

        markdown_html = markdown_to_html(self.markdown_text)
        return HtmlSanitizer().clean_html(markdown_html)

    def to_latex(self) -> str:
        latex_output = pypandoc.convert_text(
            self.markdown_text,
            to="latex",
            format="md",
        )
        return f"\\begin{{contentbox}}{latex_output}\\end{{contentbox}}"

    def to_json(self) -> dict[str, str]:
        return {"markdown_reporting_element": self.markdown_text}

    def get_context_data(self) -> ContextTypes:
        return {"text": self.convert_to_html()}


class ReportingError(ReportingElement):
    template_name = "error"

    def __init__(self, error_header: str, error_texts: list[str]):
        self.error_header = error_header
        self.error_texts = error_texts

    def get_context_data(self) -> ContextTypes:
        return {"error_header": self.error_header, "error_texts": self.error_texts}

    def to_json(self) -> ContextTypes:
        return self.get_context_data()

    def to_latex(self) -> str:
        return f"\\textbf{{{self.error_header}}}\\\\{'\\\\'.join(self.error_texts)}"


class ReportingFooter(ReportingText):
    template_name = "footer"
