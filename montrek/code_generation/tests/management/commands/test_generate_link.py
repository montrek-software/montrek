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
        self.output_dir = os.path.relpath(get_test_file_path("output_links"))
        os.makedirs(self.output_dir, exist_ok=True)
        with patch("sys.stdout", new_callable=io.StringIO):
            call_command("generate_table", self.output_dir, "mother")
            call_command("generate_table", self.output_dir, "daughter")
            call_command(
                "generate_link", self.output_dir, "daughter", self.output_dir, "mother"
            )
        with open(
            os.path.join(self.output_dir, "models", "daughter_hub_models.py")
        ) as f:
            code = f.read().replace(" ", "")
            link_field = """class DaughterHub(MontrekHubABC):
    link_daughter_mother = models.ManyToManyField(
        to=MotherHub,
        through="LinkDaughterMother",
        related_name="link_mother_daughter",
    )"""
            self.assertIn(link_field.replace(" ", ""), code)
            link_class = """class LinkDaughterMother(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey(DaughterHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(MotherHub, on_delete=models.CASCADE)"""
            self.assertIn(link_class.replace(" ", ""), code)
        with open(
            os.path.join(self.output_dir, "repositories", "daughter_repositories.py")
        ) as f:
            code = f.read().replace(" ", "")
        shutil.rmtree(self.output_dir)
