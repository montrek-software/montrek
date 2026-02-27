import io
import os
import shutil

from django.core.management import call_command
from django.test import TestCase

from code_generation.tests import get_test_file_path

DATA_PREFIX = "exp__file_upload__"


class TestGenerateFileUploadCommand(TestCase):
    def setUp(self):
        self.maxDiff = None
        self._cleanup_dirs = []

    def tearDown(self):
        for d in self._cleanup_dirs:
            shutil.rmtree(d, ignore_errors=True)

    def _make_output_dir(self, name: str) -> str:
        path = os.path.relpath(get_test_file_path(name))
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path, exist_ok=True)
        self._cleanup_dirs.append(path)
        return path

    def test_files_as_expected(self):
        output_dir = self._make_output_dir("output_file_upload")
        rebase = False
        with patch_stdout():
            call_command("generate_file_upload", output_dir, "test_entity")

        expected_paths = {
            "registry_hub_models": [
                "models",
                "test_entity_registry_hub_models.py",
            ],
            "registry_sat_models": [
                "models",
                "test_entity_registry_sat_models.py",
            ],
            "registry_repositories": [
                "repositories",
                "test_entity_registry_repositories.py",
            ],
            "registry_managers": [
                "managers",
                "test_entity_registry_managers.py",
            ],
            "registry_processor": [
                "managers",
                "test_entity_registry_processor.py",
            ],
            "registry_upload_manager": [
                "managers",
                "test_entity_registry_upload_manager.py",
            ],
            "registry_pages": ["pages", "test_entity_registry_pages.py"],
            "registry_views": ["views", "test_entity_registry_views.py"],
            "registry_urls": ["urls", "test_entity_registry_urls.py"],
            "registry_urls_init": ["urls", "__init__.py"],
            "registry_hub_factories": [
                "tests",
                "factories",
                "test_entity_registry_hub_factories.py",
            ],
            "registry_sat_factories": [
                "tests",
                "factories",
                "test_entity_registry_sat_factories.py",
            ],
            "registry_view_tests": [
                "tests",
                "views",
                "test_test_entity_registry_views.py",
            ],
        }

        for path_list in expected_paths.values():
            test_file_name = get_test_file_path(
                DATA_PREFIX + "__".join(path_list).replace(".", "_")
            )
            path = os.path.join(output_dir, *path_list)
            self.assertTrue(os.path.exists(path), msg=f"Missing: {path}")
            test_file_path = get_test_file_path(test_file_name)
            if rebase:
                shutil.copyfile(path, test_file_path)
            with open(path) as f:
                actual = f.read().strip()
            with open(test_file_name) as f:
                expected = f.read().strip()
            self.assertEqual(actual, expected, msg=f"Mismatch in {path}")

    def test_handle_camel_case_prefix(self):
        output_dir = self._make_output_dir("output_file_upload_camel_case")
        with patch_stdout():
            call_command("generate_file_upload", output_dir, "TestEntity")

        expected_paths = {
            "registry_hub_models": [
                "models",
                "test_entity_registry_hub_models.py",
            ],
            "registry_views": ["views", "test_entity_registry_views.py"],
            "registry_view_tests": [
                "tests",
                "views",
                "test_test_entity_registry_views.py",
            ],
        }

        for path_list in expected_paths.values():
            path = os.path.join(output_dir, *path_list)
            self.assertTrue(os.path.exists(path), msg=f"Missing: {path}")
            with open(path) as f:
                self.assertIn("TestEntity", f.read())


def patch_stdout():
    import unittest.mock

    return unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
