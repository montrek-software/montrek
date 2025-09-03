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
            repo_change = """class DaughterRepository(MontrekRepository):
    hub_class=DaughterHub

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            MotherSatellite,
            LinkDaughterMother,
            ["hub_entity_id"],
            rename_field_map={'hub_entity_id':'mother_id'}
        )"""
            self.assertIn(repo_change.replace(" ", ""), code)
            expected_import_statements = (
                "from code_generation.tests.data.output_links.models.mother_sat_models import MotherSatellite\n",
                "from code_generation.tests.data.output_links.models.daughter_hub_models import LinkDaughterMother\n",
            )
            for import_statement in expected_import_statements:
                self.assertIn(
                    import_statement.replace(" ", ""),
                    code,
                )
        with open(
            os.path.join(
                self.output_dir, "tests", "factories", "daughter_sat_factories.py"
            )
        ) as f:
            code = f.read().replace(" ", "")
            post_generate_code = """def mother(self, create, extracted, **kwargs):
    if not create:
        return
    if not extracted:
        return
    self.hub_entity.link_daughter_mother.add(extracted.hub_entity)
    """
            self.assertIn(post_generate_code.replace(" ", ""), code)
        shutil.rmtree(self.output_dir)
