from django.test import TestCase

from file_upload.managers.field_map_file_upload_processor import (
    FieldMapFileUploadProcessor,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from baseclasses.managers.montrek_manager import MontrekManager


class MockMontrekManager(MontrekManager):
    pass


class ReadErrorFieldMapFileUploadProcessor(FieldMapFileUploadProcessor):
    manager_class = MockMontrekManager

    def get_source_df_from_file(self, file_path: str):
        raise RuntimeError("cannot read file")


class TestFieldMapFileUploadProcessor(TestCase):
    def test_read_error_is_handled(self):
        registry_sat = FileUploadRegistryStaticSatelliteFactory()
        processor = ReadErrorFieldMapFileUploadProcessor(registry_sat.hub_entity, {})

        self.assertFalse(processor.process("file_path"))
        self.assertIn("cannot read file", processor.message)
