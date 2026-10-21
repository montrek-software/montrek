from pathlib import Path
from unittest import mock

import plotly.graph_objects as go
from django.conf import settings
from django.test import TestCase
from reporting.core import workbench
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.tests import mocks


class FileWritingElement(mocks.MockReportElement):
    """Writes an include into the workbench while rendered, as a plot does."""

    written: list[Path] = []

    def to_latex(self):
        path = workbench.current() / "include.txt"
        path.write_text("include")
        self.written.append(path)
        return super().to_latex()


class TestWorkbench(TestCase):
    def test_outside_a_run_uses_workbench_path(self):
        self.assertEqual(workbench.current(), Path(settings.WORKBENCH_PATH))

    def test_a_run_has_its_own_directory_and_removes_it(self):
        with workbench.activate() as directory:
            self.assertEqual(workbench.current(), directory)
            (directory / "file.txt").write_text("x")
        self.assertFalse(directory.exists())
        self.assertEqual(workbench.current(), Path(settings.WORKBENCH_PATH))

    def test_compile_writes_includes_into_the_run_and_removes_them(self):
        FileWritingElement.written = []
        manager = mocks.MockMontrekReportManager(session_data={})
        manager.append_report_element(FileWritingElement())
        pdf_path = LatexReportManager(manager).compile_report()

        self.assertIsNotNone(pdf_path)
        self.assertTrue(Path(pdf_path).is_file())
        [include] = FileWritingElement.written
        self.assertNotEqual(include.parent, Path(settings.WORKBENCH_PATH))
        self.assertFalse(include.parent.exists())

    def test_compile_removes_the_run_when_it_fails(self):
        seen: list[Path] = []

        def generate_report() -> str:
            seen.append(workbench.current())
            return ""

        manager = mocks.MockMontrekReportManager(session_data={})
        latex_manager = LatexReportManager(manager)
        with (
            mock.patch.object(
                latex_manager, "generate_report", side_effect=generate_report
            ),
            mock.patch(
                "reporting.managers.latex_report_manager.subprocess.run",
                side_effect=OSError("no xelatex"),
            ),
            self.assertRaises(OSError),
        ):
            latex_manager.compile_report()
        [directory] = seen
        self.assertNotEqual(directory, Path(settings.WORKBENCH_PATH))
        self.assertFalse(directory.exists())

    def test_plot_image_goes_into_the_run(self):
        plot = mocks.MockComprehensiveReportManager(session_data={}).plot(width=0.5)
        with (
            mock.patch.object(go.Figure, "write_image") as write_image,
            workbench.activate() as directory,
        ):
            latex = plot.to_latex()
        image_path = Path(write_image.call_args.args[0])
        self.assertEqual(image_path.parent, directory)
        self.assertIn(str(image_path), latex)
