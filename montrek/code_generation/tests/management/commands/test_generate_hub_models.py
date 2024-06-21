import os
import tempfile
from django.test import TestCase
from django.core.management import call_command

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


class GenerateHubModelsCommandTest(TestCase):
    def test_generate_hub_models(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_hub_models.py")
            call_command("generate_hub_models", "TestHub", output_path)

            self.assertTrue(os.path.exists(output_path))
            with open(output_path) as f:
                content = f.read()
