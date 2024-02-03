import os
from django.test import TestCase
from account.managers.onvista_file_upload_manager import (
    OnvistaFileUploadDepotProcessor,
    OnvistaFileUploadProcessor,
)
from account.managers.not_implemented_processor import NotImplementedFileUploadProcessor


class TestOnvistaFileUploadManager(TestCase):
    def test_default_processor(self):
        processor = OnvistaFileUploadProcessor(None)
        self.assertEqual(processor.message, "Not implemented")

    def test_no_type_detectable(self):
        processor = OnvistaFileUploadProcessor(None)
        test_path = "/tmp/test_file.csv"
        with open(test_path, "w") as f:
            f.write("UNKNOWN")
        result = processor.pre_check(test_path)
        self.assertEqual(result, False)
        self.assertEqual(processor.message, "File cannot be processed")
        self.assertIsInstance(processor.subprocessor, NotImplementedFileUploadProcessor)

    def test_empty_file(self):
        processor = OnvistaFileUploadProcessor(None)
        test_path = "/tmp/test_file.csv"
        with open(test_path, "w"):
            ...
        result = processor.pre_check(test_path)
        self.assertEqual(result, False)
        self.assertEqual(processor.message, "File cannot be processed")
        self.assertIsInstance(processor.subprocessor, NotImplementedFileUploadProcessor)

    def test_depotuebersicht_processor(self):
        processor = OnvistaFileUploadProcessor(None)
        test_path = os.path.join(os.path.dirname(__file__), "data", "onvista_test.csv")
        result = processor.pre_check(test_path)
        self.assertEqual(result, True)
        self.assertIsInstance(processor.subprocessor, OnvistaFileUploadDepotProcessor)
        result = processor.process(test_path, None)
        self.assertEqual(result, True)
        self.assertEqual(processor.subprocessor.input_data_df.shape, (3, 24))
