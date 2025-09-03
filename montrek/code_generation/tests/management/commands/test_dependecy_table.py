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
        with open(
            os.path.join(self.output_dir, "tests", "views", "test_mother_views.py")
        ) as f:
            code = f.read().replace(" ", "")
            expected_code = """class TestMotherDaughtersListView(vtc.MontrekListViewTestCase):
    viewname = "mother_daughters_list"
    view_class = views.MotherDaughtersListView
    expected_no_of_rows = 5

    def build_factories(self):
        self.mother_factory = MotherSatelliteFactory.create()
        DaughterSatelliteFactory.create_batch(
            5, mother=self.mother_factory
        )
        other_mother_factory = MotherSatelliteFactory.create()
        DaughterSatelliteFactory.create_batch(
            5, mother=other_mother_factory
        )

    def url_kwargs(self):
        return {"pk": self.mother_factory.get_hub_value_date().pk}"""
            self.assertIn(expected_code.replace(" ", ""), code)
        shutil.rmtree(self.output_dir)
