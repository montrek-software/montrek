import io
import os
import shutil
from unittest.mock import patch

from code_generation.tests import get_test_file_path
from django.core.management import call_command
from django.test import TestCase


class TestGenerateLinkCommand(TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_insertions_in_files(self):
        self.output_dir = os.path.relpath(get_test_file_path("output_dependecy_table"))
        os.makedirs(self.output_dir, exist_ok=True)
        with patch("sys.stdout", new_callable=io.StringIO):
            call_command("generate_table", self.output_dir, "mother")
            call_command("generate_table", self.output_dir, "daughter")
            call_command(
                "generate_dependency_table",
                self.output_dir,
                "daughter",
                self.output_dir,
                "mother",
            )
        shutil.rmtree(self.output_dir)
