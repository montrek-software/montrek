import io
import os
import shutil
from unittest.mock import patch

from code_generation.tests import get_test_file_path
from django.core.management import call_command
from django.test import TestCase


class TestGenerateTableCommand(TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_files_as_expected(self):
        output_dir = os.path.relpath(get_test_file_path("output"))
        os.makedirs(output_dir, exist_ok=True)
        rebase = False
        with patch("sys.stdout", new_callable=io.StringIO):
            call_command("generate_table", output_dir, "company")

        expected_paths = {
            "forms": ["forms", "company_forms.py"],
            "hub_factories": ["tests", "factories", "company_hub_factories.py"],
            "hub_models": ["models", "company_hub_models.py"],
            "managers": ["managers", "company_managers.py"],
            "models_init": ["models", "__init__.py"],
            "pages": ["pages", "company_pages.py"],
            "repositories": ["repositories", "company_repositories.py"],
            "sat_factories": ["tests", "factories", "company_sat_factories.py"],
            "sat_models": ["models", "company_sat_models.py"],
            "urls": ["urls", "company_urls.py"],
            "urls_init": ["urls", "__init__.py"],
            "view_tests": ["tests", "views", "test_company_views.py"],
            "views": ["views", "company_views.py"],
            "views_init": ["views", "__init__.py"],
        }

        for path_list in expected_paths.values():
            test_file_name = f"exp__{'__'.join(path_list)}"
            # Real .py files will be formatted by git hooks which makes comparing them difficult
            test_file_name = test_file_name.replace(".", "_")
            path = os.path.join(output_dir, *path_list)
            self.assertTrue(os.path.exists(path))
            test_file_path = get_test_file_path(test_file_name)
            if rebase:
                shutil.copyfile(path, test_file_path)
            actual = open(path).read().strip()
            expected = open(test_file_path).read().strip()
            self.assertEqual(actual, expected)
        shutil.rmtree(output_dir)

    def test_handle_camel_case_prefixes(self):
        output_dir = os.path.relpath(
            get_test_file_path("output_handle_camel_case_prefixes")
        )
        os.makedirs(output_dir, exist_ok=True)
        with patch("sys.stdout", new_callable=io.StringIO):
            call_command("generate_table", output_dir, "TestCompany")
        expected_paths = {
            "forms": ["forms", "test_company_forms.py"],
            "hub_models": ["models", "test_company_hub_models.py"],
            "managers": ["managers", "test_company_managers.py"],
            "models_init": ["models", "__init__.py"],
            "pages": ["pages", "test_company_pages.py"],
            "repositories": ["repositories", "test_company_repositories.py"],
            "sat_models": ["models", "test_company_sat_models.py"],
            "urls": ["urls", "test_company_urls.py"],
            "urls_init": ["urls", "__init__.py"],
            "views": ["views", "test_company_views.py"],
            "views_init": ["views", "__init__.py"],
        }
        expected_paths = {
            k: os.path.join(output_dir, *v) for k, v in expected_paths.items()
        }
        for path in expected_paths.values():
            self.assertTrue(os.path.exists(path))
            if "__init__" not in path:
                with open(path) as f:
                    self.assertIn("TestCompany", f.read())
        shutil.rmtree(output_dir)


class TestStartMontrekAppCommand(TestCase):
    def setUp(self):
        self.new_app_name = "new_app"
        self.maxDiff = None

    def test_startmontrekapp__w_path(self):
        output_dir = os.path.relpath(get_test_file_path("output_start_app"))
        os.makedirs(output_dir, exist_ok=True)
        with patch("sys.stdout", new_callable=io.StringIO):
            call_command("start_montrek_app", self.new_app_name, path=output_dir)
        self._test_app_assertions(os.path.join(output_dir, self.new_app_name))
        with open(os.path.join(output_dir, self.new_app_name, "apps.py")) as f:
            search_str = (
                f"name = '{output_dir.replace(os.sep, '.')}.{self.new_app_name}'"
            )
            self.assertIn(search_str, f.read())
        shutil.rmtree(output_dir)

    def test_startmontrekapp__wo_path(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            call_command("start_montrek_app", self.new_app_name)
        self._test_app_assertions(self.new_app_name)
        shutil.rmtree(self.new_app_name)

    def _test_app_assertions(self, new_app_path: str):
        self.assertTrue(os.path.exists(new_app_path))
        existing_files = ("migrations", "apps.py", "admin.py", "__init__.py")
        for existing_file in existing_files:
            with self.subTest(file=existing_file):
                self.assertTrue(
                    os.path.exists(os.path.join(new_app_path, existing_file))
                )
        removed_files = ("tests.py", "models.py", "views.py")
        for removed_file in removed_files:
            with self.subTest(file=removed_file):
                self.assertFalse(
                    os.path.exists(os.path.join(new_app_path, removed_file))
                )
