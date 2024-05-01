from django.conf import settings
from django.utils.safestring import mark_safe
import os
from typing import Protocol
from baseclasses.managers.montrek_manager import MontrekManager
from django.template import Template, Context
import subprocess
import tempfile
import shutil

from baseclasses.dataclasses.montrek_message import MontrekMessageError


class ReportElementProtocol(Protocol):
    def to_html(self) -> str:
        ...

    def to_latex(self) -> str:
        ...


class MontrekReportManager(MontrekManager):
    def __init__(self, session_data: dict[str, str], **kwargs) -> None:
        super().__init__(session_data=session_data, **kwargs)
        self._report_elements = []

    @property
    def report_elements(self) -> list[ReportElementProtocol, ...]:
        return self._report_elements

    def append_report_element(self, report_element: ReportElementProtocol) -> None:
        self._report_elements.append(report_element)

    def generate_report(self) -> str:
        return "MontrekReportManager: No report generated!!"


class LatexReportManager(MontrekReportManager):
    latex_template = "montrek_base_template.tex"

    @property
    def document_name(self):
        return "document"

    def generate_report(self) -> str:
        context_data = self.get_context()
        for key, value in context_data.items():
            context_data[key] = mark_safe(value)
        context = Context(context_data)
        template = Template(self.read_template())
        return template.render(context)

    def get_context(self) -> dict:
        content = ""
        for report_element in self.report_elements:
            content += report_element.to_latex()
        return {"content": content}

    def read_template(self) -> str:
        template_path = self._get_template_path()
        if template_path is None:
            raise FileNotFoundError(f"Template {self.latex_template} not found")
        with open(template_path, "r") as file:
            return file.read()

    def compile_report(self) -> str | None:
        report_str = self.generate_report()
        output_dir = os.path.join(settings.MEDIA_ROOT, "latex")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Path to the temporary LaTeX file
            latex_file_path = os.path.join(tmpdirname, "document.tex")

            # Write the LaTeX code to a file
            with open(latex_file_path, "w") as f:
                f.write(report_str)

            # Compile the LaTeX file into a PDF using xelatex
            try:
                subprocess.run(
                    [
                        "xelatex",
                        "-output-directory",
                        tmpdirname,
                        "-interaction=nonstopmode",
                        latex_file_path,
                    ],
                    capture_output=True,
                    check=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                error_message = self.get_xelatex_error_message(e.stdout)
                self.messages.append(MontrekMessageError(message=error_message))
                self.messages.append(MontrekMessageError(message=report_str))
                return None

            # Define the source PDF path (assuming the output PDF has the same name as the .tex file, but with .pdf extension)
            pdf_file_path = os.path.join(tmpdirname, "document.pdf")

            # Define the destination PDF path
            output_pdf_path = os.path.join(output_dir, "document.pdf")

            # Move the PDF to the output directory
            shutil.move(pdf_file_path, output_pdf_path)

            # Return the path to the output PDF file
            return output_pdf_path

    def _get_template_path(self) -> str | None:
        for template_dir in settings.TEMPLATES[0]["DIRS"]:
            potential_path = os.path.join(
                template_dir, "latex_templates", self.latex_template
            )
            if os.path.exists(potential_path):
                return potential_path
        return None

    def get_xelatex_error_message(self, stdout: str) -> str:
        for line in stdout.split("\n"):
            if "LaTeX Error:" in line:
                return line
        return stdout
