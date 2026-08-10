import io
import os
import shutil
import unittest.mock

from django.core.management import call_command
from django.test import TestCase

from code_generation.tests import get_test_file_path

DATA_PREFIX = "exp__file_export__"

EXPECTED_PATHS = {
    "export_registry_hub_models": [
        "models",
        "test_entity_export_registry_hub_models.py",
    ],
    "export_registry_sat_models": [
        "models",
        "test_entity_export_registry_sat_models.py",
    ],
    "export_registry_repositories": [
        "repositories",
        "test_entity_export_registry_repositories.py",
    ],
    "export_registry_managers": [
        "managers",
        "test_entity_export_registry_managers.py",
    ],
    "export_processor": ["managers", "test_entity_export_processor.py"],
    "export_manager": ["managers", "test_entity_export_manager.py"],
    "export_registry_pages": ["pages", "test_entity_export_registry_pages.py"],
    "export_registry_views": ["views", "test_entity_export_registry_views.py"],
    "export_registry_urls": ["urls", "test_entity_export_registry_urls.py"],
    "export_registry_urls_init": ["urls", "__init__.py"],
    "export_registry_hub_factories": [
        "tests",
        "factories",
        "test_entity_export_registry_hub_factories.py",
    ],
    "export_registry_sat_factories": [
        "tests",
        "factories",
        "test_entity_export_registry_sat_factories.py",
    ],
    "export_registry_view_tests": [
        "tests",
        "views",
        "test_test_entity_export_registry_views.py",
    ],
}


def patch_stdout():
    return unittest.mock.patch("sys.stdout", new_callable=io.StringIO)


class TestGenerateFileExportCommand(TestCase):
    rebase = False

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
        output_dir = self._make_output_dir("output_file_export")
        with patch_stdout():
            call_command("generate_file_export", output_dir, "test_entity")

        for path_list in EXPECTED_PATHS.values():
            expected_file_path = get_test_file_path(
                DATA_PREFIX + "__".join(path_list).replace(".", "_")
            )
            path = os.path.join(output_dir, *path_list)
            self.assertTrue(os.path.exists(path), msg=f"Missing: {path}")
            if self.rebase:
                shutil.copyfile(path, expected_file_path)
            with open(path) as f:
                actual = f.read().strip()
            with open(expected_file_path) as f:
                expected = f.read().strip()
            self.assertEqual(actual, expected, msg=f"Mismatch in {path}")

    def test_init_files_generated(self):
        output_dir = self._make_output_dir("output_file_export_init")
        with patch_stdout():
            call_command("generate_file_export", output_dir, "test_entity")

        for path_list in EXPECTED_PATHS.values():
            init_path = os.path.join(output_dir, *path_list[:-1], "__init__.py")
            self.assertTrue(os.path.exists(init_path), msg=f"Missing: {init_path}")

    def test_handle_camel_case_prefix(self):
        output_dir = self._make_output_dir("output_file_export_camel_case")
        with patch_stdout():
            call_command("generate_file_export", output_dir, "TestEntity")

        expected_paths = {
            "export_registry_hub_models": [
                "models",
                "test_entity_export_registry_hub_models.py",
            ],
            "export_processor": ["managers", "test_entity_export_processor.py"],
            "export_registry_views": [
                "views",
                "test_entity_export_registry_views.py",
            ],
            "export_registry_view_tests": [
                "tests",
                "views",
                "test_test_entity_export_registry_views.py",
            ],
        }

        for path_list in expected_paths.values():
            path = os.path.join(output_dir, *path_list)
            self.assertTrue(os.path.exists(path), msg=f"Missing: {path}")
            with open(path) as f:
                self.assertIn("TestEntity", f.read())

    def test_replace_does_not_append(self):
        output_dir = self._make_output_dir("output_file_export_replace")
        with patch_stdout():
            call_command("generate_file_export", output_dir, "test_entity")
            call_command(
                "generate_file_export", output_dir, "test_entity", replace=True
            )

        path = os.path.join(output_dir, *EXPECTED_PATHS["export_processor"])
        with open(path) as f:
            content = f.read()
        self.assertEqual(content.count("class TestEntityFileExportProcessor"), 1)
