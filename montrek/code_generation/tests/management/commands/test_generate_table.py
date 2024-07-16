import os
import tempfile
from django.test import TestCase
from django.core.management import call_command


class GenerateTableCommandTest(TestCase):
    def test_files_are_created(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            call_command("generate_table", temp_dir, "company")

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
            }
            expected_paths = {
                k: os.path.join(temp_dir, *v) for k, v in expected_paths.items()
            }

            for path in expected_paths.values():
                self.assertTrue(os.path.exists(path))
