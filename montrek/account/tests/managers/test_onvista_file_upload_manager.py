from django.test import TestCase
from account.managers.onvista_file_upload_manager import OnvistaFileUploadProcessor


class TestOnvistaFileUploadManager(TestCase):
    def test_default_processor(self):
        processor = OnvistaFileUploadProcessor(None)
        self.assertEqual(processor.message, "Not implemented")

        self.assertEqual(processor.pre_check("test"), False)
