from django.test import SimpleTestCase
from file_upload.modules.unattended_upload_registry import UnattendedUploadRegistry

from montrek_example.managers.a1_file_upload_manager import A1FileUploadManager


class TestUnattendedUploadRegistry(SimpleTestCase):
    def test_choices_list_the_opted_in_example_manager(self):
        choices = dict(UnattendedUploadRegistry.choices())
        key = UnattendedUploadRegistry.key(A1FileUploadManager)
        self.assertEqual(choices[key], "Example A1 upload")
