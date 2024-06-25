import os
import tempfile
from django.test import TestCase
from django.core.management import call_command


class GenerateSatelliteModelsCommandTest(TestCase):
    def test_generate_satellite_models(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            call_command("generate_satellite_models", temp_dir, "test")

            expected_output_path = os.path.join(
                temp_dir, "models", "test_satellite_models.py"
            )
            self.assertTrue(os.path.exists(expected_output_path))
