import shutil
import os
from django.test import TestCase
from django.core.management import call_command

from unittest.mock import patch
import io
from code_generation.tests import get_test_file_path


class TestGenerateTableCommand(TestCase):
    def setUp(self):
        self.output_dir = os.path.relpath(get_test_file_path("output"))
        self.maxDiff = None
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test_files_as_expected(self):
        rebase = False
        with patch("sys.stdout", new_callable=io.StringIO):
            call_command("generate_table", self.output_dir, "company")

        expected_paths = {
            "forms": ["forms", "company_forms.py"],
            "hub_models": ["models", "company_hub_models.py"],
            "managers": ["managers", "company_managers.py"],
            "models_init": ["models", "__init__.py"],
            "pages": ["pages", "company_pages.py"],
            "repositories": ["repositories", "company_repositories.py"],
            "sat_models": ["models", "company_sat_models.py"],
            "urls": ["urls", "company_urls.py"],
            "urls_init": ["urls", "__init__.py"],
            "views": ["views", "company_views.py"],
            "views_init": ["views", "__init__.py"],
            "hub_factories": ["tests", "factories", "company_hub_factories.py"],
            "sat_factories": ["tests", "factories", "company_sat_factories.py"],
        }

        for path_list in expected_paths.values():
            test_file_name = f"exp__{'__'.join(path_list)}"
            # Real .py files will be formatted by git hooks which makes comparing them difficult
            test_file_name = test_file_name.replace(".", "_")
            path = os.path.join(self.output_dir, *path_list)
            self.assertTrue(os.path.exists(path))
            test_file_path = get_test_file_path(test_file_name)
            if rebase:
                shutil.copyfile(path, test_file_path)
            actual = open(path).read().strip()
            expected = open(test_file_path).read().strip()
            self.assertEqual(actual, expected)

    def test_handle_camel_case_prefixes(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            call_command("generate_table", self.output_dir, "TestCompany")
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
            k: os.path.join(self.output_dir, *v) for k, v in expected_paths.items()
        }
        for path in expected_paths.values():
            self.assertTrue(os.path.exists(path))
            if "__init__" not in path:
                with open(path) as f:
                    self.assertIn("TestCompany", f.read())
