import os
from django.test import TestCase
from account.managers.account_file_upload_manager import AccountFileUploadProcessor
from account.tests.factories.account_factories import AccountHubFactory
from account.tests.factories.account_factories import BankAccountStaticSatelliteFactory
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)


class TestDKBAccountFileUploadManager(TestCase):
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
        result = account_file_upload_processor.process(
            self.test_csv_path, self.upload_registry.hub_entity
        )
        self.assertEqual(
            account_file_upload_processor.message,
            "DKB upload was successful (15 transactions)",
        )
        self.assertEqual(result, True)
        file_upload_registries = (
            self.account_hub.link_account_file_upload_registry.first()
        )
        self.assertEqual(file_upload_registries, self.upload_registry.hub_entity)

    def test_pre_check_fails(self):
        acc_no_iban = AccountHubFactory()
        acc_no_iban.link_account_credit_institution.add(
            self.credit_institution_sat.hub_entity
        )
        bacc = BankAccountStaticSatelliteFactory(
            hub_entity=acc_no_iban,
            bank_account_iban="DE12345678901234567890"
        )
        account_file_upload_processor = AccountFileUploadProcessor(
            **{"pk": acc_no_iban.pk}
        )
        result = account_file_upload_processor.pre_check(self.test_csv_path)
        self.assertEqual(result, False)
        self.assertEqual(
            account_file_upload_processor.message,
            "IBAN in file (DE12345643) does not match account iban (DE12345678901234567890)",
        )

    def test_post_check_fails(self):
        account_file_upload_processor = AccountFileUploadProcessor(
            **{"pk": self.account_hub.pk}
        )
        result = account_file_upload_processor.process(
            self.test_csv_path, self.upload_registry.hub_entity
        )
        result = account_file_upload_processor.post_check(
            self.test_csv_path
        )
        self.assertEqual(result, False)
        self.assertEqual(
            account_file_upload_processor.message,
            "Bank account value and value from file differ by -5,276.30 EUR"
        )

