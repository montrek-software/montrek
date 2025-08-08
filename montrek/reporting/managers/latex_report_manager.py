import logging
import os
import shutil
import subprocess  # nosec B404
from pathlib import Path

from baseclasses.dataclasses.montrek_message import MontrekMessageError
from baseclasses.sanitizer import HtmlSanitizer
from django.conf import settings
from django.template import Context, Template
from django.utils.safestring import mark_safe
from reporting.constants import WORKBENCH_PATH
from reporting.core.reporting_colors import Color, ReportingColors
from reporting.core.reporting_text import ClientLogo
from reporting.managers.montrek_report_manager import MontrekReportManager

logger = logging.getLogger(__name__)


class LatexReportManager:
    latex_template = "montrek_base_template.tex"

    def __init__(self, report_manager: MontrekReportManager):
        self.report_manager = report_manager

    def generate_report(self) -> str:
        context_data = self.get_context()
        context_data.update(self.get_layout_data())
        for key, value in context_data.items():
            context_data[key] = mark_safe(
                HtmlSanitizer().clean_html(value)
            )  # nosec B308 B703 - value is sanitized
        context_data["footer_text"] = self.report_manager.footer_text.to_latex()
        context_data["watermark_text"] = "Draft" if self.report_manager.draft else ""
        context = Context(context_data)
        template = Template(self.read_template())
        return template.render(context)

    def get_context(self) -> dict:
        return {
            "content": self.report_manager.to_latex(),
        }

    def get_layout_data(self) -> dict:
        return {
            "montrek_logo": os.path.join(
                settings.BASE_DIR,
                "baseclasses",
                "static",
                "logos",
                "montrek_logo_variant.png",
            ),
            "client_logo": ClientLogo().to_latex(),
            "document_title": self.report_manager.document_title,
            "footer_text": self.report_manager.footer_text,
            "colors": self.get_colors(),
        }

    def get_colors(self) -> str:
        colorstr = ""
        for color in ReportingColors.COLOR_PALETTE_SKIM:
            color_hex = color.hex.replace("#", "")
            colorstr += f"\\definecolor{{{color.name}}}{{HTML}}{{{color_hex}}}\n"

        primary_color = Color("primary", settings.PRIMARY_COLOR)
        secondary_color = Color("secondary", settings.SECONDARY_COLOR)
        primary_color_hex = primary_color.hex.replace("#", "")
        secondary_color_hex = secondary_color.hex.replace("#", "")
        colorstr += f"\\definecolor{{primary}}{{HTML}}{{{primary_color_hex}}}\n"
        colorstr += f"\\definecolor{{secondary}}{{HTML}}{{{secondary_color_hex}}}\n"
        primary_light = ReportingColors.lighten_color(primary_color)
        secondary_light = ReportingColors.lighten_color(secondary_color)
        primary_light_hex = primary_light.hex.replace("#", "")
        secondary_light_hex = secondary_light.hex.replace("#", "")
        colorstr += f"\\definecolor{{primary_light}}{{HTML}}{{{primary_light_hex}}}\n"
        colorstr += (
            f"\\definecolor{{secondary_light}}{{HTML}}{{{secondary_light_hex}}}\n"
        )
        return colorstr

    def read_template(self) -> str:
        template_path = self._get_template_path()
        if template_path is None:
            raise FileNotFoundError(f"Template {self.latex_template} not found")
        with open(template_path, "r") as file:
            return file.read()

    def compile_report(self) -> str | None:
        report_str = self.generate_report()

        # Ensure the output folders exist
        output_dir = os.path.join(settings.MEDIA_ROOT, "latex")
        os.makedirs(output_dir, exist_ok=True)
        WORKBENCH_PATH.mkdir(parents=True, exist_ok=True)

        # Paths for .tex and .pdf files in the workbench
        tex_filename = f"{self.report_manager.document_name}.tex"
        pdf_filename = f"{self.report_manager.document_name}.pdf"

        latex_file_path = WORKBENCH_PATH / tex_filename
        pdf_file_path = WORKBENCH_PATH / pdf_filename
        output_pdf_path = Path(output_dir) / pdf_filename

        # Write the LaTeX code to the .tex file
        with open(latex_file_path, "w") as f:
            f.write(report_str)

        # Compile the LaTeX file into a PDF using xelatex
        try:
            subprocess.run(
                [
                    "/usr/bin/xelatex",
                    "-output-directory",
                    str(WORKBENCH_PATH),
                    "-interaction=nonstopmode",
                    str(latex_file_path),
                ],
                capture_output=True,
                check=True,
                text=True,
            )  # nosec B603
        except subprocess.CalledProcessError as e:
            if settings.IS_TEST_RUN:
                logger.error(e.stdout)
                raise e
            logger.error(report_str)
            error_message = self.get_xelatex_error_message(e.stdout)
            self.report_manager.messages.append(
                MontrekMessageError(message=error_message)
            )
            self.report_manager.messages.append(MontrekMessageError(message=report_str))
            return None

        # Move the compiled PDF to the final output directory
        shutil.move(str(pdf_file_path), str(output_pdf_path))
        # Clear the workbench directory (but preserve the folder itself)
        for item in WORKBENCH_PATH.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        return str(output_pdf_path)

    def _get_template_path(self) -> str | None:
        for template_dir in settings.TEMPLATES[0]["DIRS"]:
            potential_path = os.path.join(
                settings.BASE_DIR, template_dir, "latex_templates", self.latex_template
            )
            if os.path.exists(potential_path):
                return potential_path
        return None

    def get_xelatex_error_message(self, stdout: str) -> str:
        for line in stdout.split("\n"):
            if "LaTeX Error:" in line:
                return line
        return stdout
