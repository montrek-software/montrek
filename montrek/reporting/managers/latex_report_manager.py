import logging
import os
import subprocess  # nosec B404
from pathlib import Path

from baseclasses.dataclasses.montrek_message import MontrekMessageError
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
            context_data[key] = mark_safe(value)  # nosec B308 B703 - value is sanitized
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

        output_dir = Path(settings.MEDIA_ROOT) / "latex"
        output_dir.mkdir(parents=True, exist_ok=True)
        WORKBENCH_PATH.mkdir(parents=True, exist_ok=True)

        tex_filename = f"{self.report_manager.document_name}.tex"
        pdf_filename = f"{self.report_manager.document_name}.pdf"

        latex_file_path = WORKBENCH_PATH / tex_filename
        pdf_file_path = WORKBENCH_PATH / pdf_filename
        output_pdf_path = output_dir / pdf_filename
        log_path = WORKBENCH_PATH / f"{self.report_manager.document_name}.log"

        # Write LaTeX file explicitly as UTF-8 (XeLaTeX handles UTF-8 well)
        with open(latex_file_path, "w", encoding="utf-8") as f:
            f.write(report_str)

        try:
            proc = subprocess.run(
                [
                    "/usr/bin/xelatex",
                    "-output-directory",
                    str(WORKBENCH_PATH),
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    str(latex_file_path),
                ],
                capture_output=True,
                check=True,
                text=False,  # capture raw bytes to avoid UnicodeDecodeError
                env={**os.environ, "LANG": os.environ.get("LANG", "C.UTF-8")},
                cwd=str(WORKBENCH_PATH),
            )  # nosec B603

        except subprocess.CalledProcessError as e:
            # Decode safely for the exception message
            err = (e.stderr or b"") + b"\n" + (e.stdout or b"")
            err_txt = err.decode("latin-1", errors="replace")
            # Optionally dump to .log for debugging
            try:
                log_path.write_text(err_txt, encoding="utf-8", errors="replace")
            except (OSError, UnicodeError) as log_exc:
                # Writing the debug log isn't critical; warn and continue.
                logger.warning("Failed to write LaTeX log to %s: %s", log_path, log_exc)
            self.report_manager.messages.append(
                MontrekMessageError(
                    message=f"LaTeX compilation failed. See log at {log_path}.\n{err_txt[-4000:]}"
                )
            )
            return None

        # Move/copy the resulting PDF to media output
        if not pdf_file_path.exists():
            # If XeLaTeX didn't produce it, surface the log
            stdout = (proc.stdout or b"").decode("latin-1", errors="replace")
            stderr = (proc.stderr or b"").decode("latin-1", errors="replace")
            raise RuntimeError(
                f"LaTeX did not produce a PDF.\n{stdout[-2000:]}\n{stderr[-2000:]}"
            )

        output_pdf_path.write_bytes(pdf_file_path.read_bytes())
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
