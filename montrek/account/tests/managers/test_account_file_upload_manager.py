import os
from django.test import TestCase
from account.managers.account_file_upload_manager import AccountFileUploadProcessor
from account.tests.factories.account_factories import AccountHubFactory
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import FileUploadRegistryStaticSatelliteFactory


class TestAccountFileUploadManager(TestCase):
    test_csv_path = os.path.join(os.path.dirname(__file__), "data/dkb_test.csv")

    def setUp(self):
        self.account_hub = AccountHubFactory()
        self.credit_institution_sat = CreditInstitutionStaticSatelliteFactory(
            account_upload_method="dkb",
        )
        self.account_hub.link_account_credit_institution.add(
            self.credit_institution_sat.hub_entity
        )
        self.upload_registry = FileUploadRegistryStaticSatelliteFactory()

    def test_process(self):
        account_file_upload_processor = AccountFileUploadProcessor(
            **{"pk": self.account_hub.pk}
        )
        result = account_file_upload_processor.process(self.test_csv_path, self.upload_registry.hub_entity)
        self.assertEqual(
            account_file_upload_processor.message, "DKB upload was successful"
        )
        self.assertEqual(result, True)
        file_upload_registries = self.account_hub.link_account_file_upload_registry.first()
        self.assertEqual(file_upload_registries, self.upload_registry.hub_entity)
