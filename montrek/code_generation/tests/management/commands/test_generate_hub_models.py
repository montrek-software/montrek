import os
import tempfile
from django.test import TestCase
from django.core.management import call_command


class GenerateHubModelsCommandTest(TestCase):
    def test_generate_hub_models(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            call_command("generate_hub_models", temp_dir, "test")

            expected_output_path = os.path.join(
                temp_dir, "models", "test_hub_models.py"
            )
            self.assertTrue(os.path.exists(expected_output_path))
