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
            expected_code = """class TestMotherDaughtersListView(MontrekListViewTestCase):
    viewname = "mother_daughters_list"
    view_class = MotherDaughtersListView
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
            import_statements = (
                "from code_generation.tests.data.output_dependecy_table.views.mother_views import MotherDaughtersListView\n",
                "from code_generation.tests.data.output_dependecy_table.tests.factories.mother_sat_factories import MotherSatelliteFactory\n",
                "from code_generation.tests.data.output_dependecy_table.tests.factories.daughter_sat_factories import DaughterSatelliteFactory\n",
            )
            for import_statement in import_statements:
                self.assertIn(import_statement.replace(" ", ""), code)
        with open(os.path.join(self.output_dir, "views", "mother_views.py")) as f:
            code = f.read().replace(" ", "")
            expected_code = """class MotherDaughtersListView(MontrekListView):
    manager_class = MotherDaughtersTableManager
    page_class = MotherDetailsPage
    title = "Mother Daughters"
    tab = "tab_mother_daughters"

    @property
    def actions(self) -> tuple[ActionElement]:
        action_create = CreateActionElement(
            url_name = "daughter_create_from_mother",
            kwargs = {"mother_id": self.kwargs["pk"]},
            action_id="id_daughter_mother_create",
            hover_text="Create Daughter from Mother",
        )
        return (action_create,)
                """
            self.assertIn(expected_code.replace(" ", ""), code)
            import_statements = (
                "from code_generation.tests.data.output_dependecy_table.managers.mother_managers import MotherDaughtersTableManager\n",
                "from baseclasses.dataclasses.view_classes import CreateActionElement",
            )
            for import_statement in import_statements:
                self.assertIn(import_statement.replace(" ", ""), code)
        with open(os.path.join(self.output_dir, "managers", "mother_managers.py")) as f:
            code = f.read().replace(" ", "")
            expected_code = """class MotherDaughtersTableManager(DaughterTableManager):
    repository_class = MotherDaughtersRepository
                """
            self.assertIn(expected_code.replace(" ", ""), code)
            import_statements = (
                "from code_generation.tests.data.output_dependecy_table.repositories.mother_repositories import MotherDaughtersRepository\n",
                "from code_generation.tests.data.output_dependecy_table.managers.daughter_managers import DaughterTableManager\n",
            )
            for import_statement in import_statements:
                self.assertIn(import_statement.replace(" ", ""), code)
        with open(
            os.path.join(self.output_dir, "repositories", "mother_repositories.py")
        ) as f:
            code = f.read().replace(" ", "")
            expected_code = """class MotherDaughtersRepository(DaughterRepository):
    repository_class = MotherDaughtersRepository
        mother_hub = MotherHubValueDate.objects.get(
            pk=self.session_data.get("pk")
        ).hub
        query = super().receive(apply_filter).filter(mother_id=mother_hub.id)
                """
            self.assertIn(expected_code.replace(" ", ""), code)
            import_statements = (
                "from code_generation.tests.data.output_dependecy_table.repositories.daughters_repositories import DaughtersRepository\n",
            )
            for import_statement in import_statements:
                self.assertIn(import_statement.replace(" ", ""), code)
        shutil.rmtree(self.output_dir)
