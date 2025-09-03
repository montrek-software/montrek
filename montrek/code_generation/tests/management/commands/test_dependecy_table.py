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
            url_name = "mother_daughter_create",
            kwargs = {"pk": self.kwargs["pk"]},
            action_id="id_daughter_mother_create",
            hover_text="Create Daughter from Mother",
        )
        return (action_create,)
                """
            self.assertIn(expected_code.replace(" ", ""), code)
            expected_code = """class MotherDaughterCreateView(DaughterCreateView):

    def get_success_url(self):
        return reverse("mother_daughters_list", kwargs={"pk": self.kwargs["pk"]})

    def get_form(self, *args, **kwargs):
        form = super().get_form(kwargs)
        hub = MotherRepository(self.session_data).receive().get(hub__pk=self.kwargs["pk"])
        form["link_daughter_mother"].initial = hub
        return form"""
            self.assertIn(expected_code.replace(" ", ""), code)
            import_statements = (
                "from code_generation.tests.data.output_dependecy_table.managers.mother_managers import MotherDaughtersTableManager\n",
                "from code_generation.tests.data.output_dependecy_table.repositories.mother_repositories import MotherRepository\n",
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
    def receive(self, apply_filter=True):
        mother_hub = MotherHubValueDate.objects.get(
            pk=self.session_data.get("pk")
        ).hub
        return super().receive(apply_filter).filter(mother_id=mother_hub.id)
                """
            self.assertIn(expected_code.replace(" ", ""), code)
            import_statements = (
                "from code_generation.tests.data.output_dependecy_table.repositories.daughter_repositories import DaughterRepository\n",
                "from code_generation.tests.data.output_dependecy_table.models.mother_hub_models import MotherHubValueDate\n",
            )
            for import_statement in import_statements:
                self.assertIn(import_statement.replace(" ", ""), code)
        with open(os.path.join(self.output_dir, "urls", "mother_urls.py")) as f:
            code = f.read().replace(" ", "")
            expected_code = """path(
        "mother/<int:pk>/daughters/list",
        MotherDaughtersListView.as_view(),
        name="mother_daughters_list"
    ),
    path(
        "mother/<int:pk>/daughter/create",
        MotherDaughterCreateView.as_view(),
        name="mother_daughter_create"
    ),
    """
            self.assertIn(expected_code.replace(" ", ""), code)
            import_statements = (
                "from code_generation.tests.data.output_dependecy_table.views.mother_views import MotherDaughtersListView\n",
                "from code_generation.tests.data.output_dependecy_table.views.mother_views import MotherDaughterCreateView\n",
            )
            for import_statement in import_statements:
                self.assertIn(import_statement.replace(" ", ""), code)
        shutil.rmtree(self.output_dir)
