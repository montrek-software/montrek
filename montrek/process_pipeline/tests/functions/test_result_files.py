import os
import tempfile
from zipfile import ZipFile

from django.test import SimpleTestCase

from process_pipeline.functions.result_files import build_zip_file


class TestBuildZipFile(SimpleTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)

    def _write(self, relative_path: str, content: bytes = b"data") -> str:
        path = os.path.join(self.tmp_dir.name, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def test_writes_each_file_under_its_base_name(self):
        paths = [self._write("a/first.csv"), self._write("b/second.csv")]

        result = build_zip_file(paths, "export.zip")

        with ZipFile(result) as zip_file:
            self.assertEqual(sorted(zip_file.namelist()), ["first.csv", "second.csv"])

    def test_keeps_the_file_contents(self):
        paths = [self._write("a/first.csv", b"col1,col2\n")]

        result = build_zip_file(paths, "export.zip")

        with ZipFile(result) as zip_file:
            self.assertEqual(zip_file.read("first.csv"), b"col1,col2\n")

    def test_rejects_paths_that_share_a_base_name(self):
        # Both flatten to report.csv, so one would overwrite the other on extraction.
        paths = [self._write("a/report.csv"), self._write("b/report.csv")]

        with self.assertRaises(ValueError) as ctx:
            build_zip_file(paths, "export.zip")

        self.assertIn("report.csv", str(ctx.exception))

    def test_names_every_collision_in_the_error(self):
        paths = [
            self._write("a/report.csv"),
            self._write("b/report.csv"),
            self._write("a/summary.csv"),
            self._write("b/summary.csv"),
        ]

        with self.assertRaises(ValueError) as ctx:
            build_zip_file(paths, "export.zip")

        self.assertIn("report.csv", str(ctx.exception))
        self.assertIn("summary.csv", str(ctx.exception))
