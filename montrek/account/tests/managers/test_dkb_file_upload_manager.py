import os
from django.test import TestCase
from account.tests.factories.account_factories import AccountHubFactory
from account.tests.factories.account_factories import BankAccountStaticSatelliteFactory
from account.managers.dkb_file_upload_manager import DkbFileUploadProcessor
from account.repositories.account_repository import AccountRepository
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)


class TestDkbAccountFileUploadManager(TestCase):
    test_csv_path = os.path.join(os.path.dirname(__file__), "data/dkb_test.csv")

    def setUp(self):
        account_hub = AccountHubFactory()
        self.credit_institution_sat = CreditInstitutionStaticSatelliteFactory(
            account_upload_method="dkb",
        )
        account_hub.link_account_credit_institution.add(
            self.credit_institution_sat.hub_entity
        )
        upload_registry = FileUploadRegistryStaticSatelliteFactory()
        account_hub.link_account_file_upload_registry.add(upload_registry.hub_entity)
        self.account_hub = AccountRepository().std_queryset().get(pk=account_hub.pk)

    def test_process(self):
        account_file_upload_processor = DkbFileUploadProcessor(
            account_hub=self.account_hub
        )
        result = account_file_upload_processor.process(self.test_csv_path)
        self.assertEqual(
            account_file_upload_processor.message,
            "DKB upload was successful (15 transactions)",
        )
        self.assertEqual(result, True)

    def test_pre_check_fails(self):
        acc_no_iban = AccountHubFactory()
        acc_no_iban.link_account_credit_institution.add(
            self.credit_institution_sat.hub_entity
        )
        BankAccountStaticSatelliteFactory(
            hub_entity=acc_no_iban, bank_account_iban="DE12345678901234567890"
        )
        acount_hub_instance = AccountRepository().std_queryset().get(pk=acc_no_iban.pk)
        account_file_upload_processor = DkbFileUploadProcessor(
            account_hub=acount_hub_instance
        )
        result = account_file_upload_processor.pre_check(self.test_csv_path)
        self.assertEqual(result, False)
        self.assertEqual(
            account_file_upload_processor.message,
            "IBAN in file (DE12345643) does not match account iban (DE12345678901234567890)",
        )

    def test_post_check_fails(self):
        account_file_upload_processor = DkbFileUploadProcessor(
            account_hub=self.account_hub
        )
        result = account_file_upload_processor.process(self.test_csv_path)
        result = account_file_upload_processor.post_check(self.test_csv_path)
        self.assertEqual(result, False)
        self.assertEqual(
            account_file_upload_processor.message,
            "Bank account value and value from file differ by -5,276.30 EUR",
        )
