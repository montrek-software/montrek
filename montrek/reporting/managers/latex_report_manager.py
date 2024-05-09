from django.conf import settings
from django.utils.safestring import mark_safe
import os
from django.template import Template, Context
import subprocess
import tempfile
import shutil
from reporting.managers.montrek_report_manager import MontrekReportManager
from baseclasses.dataclasses.montrek_message import MontrekMessageError
from reporting.core.reporting_colors import ReportingColors


class LatexReportManager:
    latex_template = "montrek_base_template.tex"

    def __init__(self, report_manager: MontrekReportManager):
        self.report_manager = report_manager

    def generate_report(self) -> str:
        context_data = self.get_context()
        context_data.update(self.get_layout_data())
        for key, value in context_data.items():
            context_data[key] = mark_safe(value)
        context = Context(context_data)
        template = Template(self.read_template())
        print(template.render(context))
        return template.render(context)

    def get_context(self) -> dict:
        return {"content": self.report_manager.to_latex()}

    def get_layout_data(self) -> dict:
        return {
            "montrek_logo": os.path.join(
                settings.STATIC_ROOT, "logos", "montrek_logo_variant.png"
            ),
            "document_title": self.report_manager.document_title,
            "footer_text": self.report_manager.footer_text,
            "colors": self.get_colors(),
        }

    def get_colors(self) -> str:
        colorstr = ""
        for color in ReportingColors.COLOR_PALETTE:
            colorstr += f"\\definecolor{{{color.name}}}{{HTML}}{{{color.hex.replace("#",'')}}}\n"
        return colorstr

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
            latex_file_path = os.path.join(
                tmpdirname, f"{self.report_manager.document_name}.tex"
            )

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
                self.report_manager.messages.append(
                    MontrekMessageError(message=error_message)
                )
                self.report_manager.messages.append(
                    MontrekMessageError(message=report_str)
                )
                return None

            # Define the source PDF path (assuming the output PDF has the same name as the .tex file, but with .pdf extension)
            pdf_file_path = os.path.join(
                tmpdirname, f"{self.report_manager.document_name}.pdf"
            )

            # Define the destination PDF path
            output_pdf_path = os.path.join(
                output_dir, f"{self.report_manager.document_name}.pdf"
            )
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
