from django.test import TestCase
from account.managers.account_file_upload_manager import AccountFileUploadProcessor
from account.managers.onvista_file_upload_manager import OnvistaFileUploadProcessor
from account.managers.dkb_file_upload_manager import DkbFileUploadProcessor
from account.tests.factories.account_factories import AccountHubFactory
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)


class TestNoCreditInstitutionAccountFileUploadManager(TestCase):
    def test_no_ci_attached(self):
        account_hub = AccountHubFactory()
        file_upload_registry = FileUploadRegistryStaticSatelliteFactory()
        account_file_upload_processor = AccountFileUploadProcessor(
            file_upload_registry_id=file_upload_registry.pk,
            **{"pk": account_hub.pk},
        )
        self.assertEqual(
            account_file_upload_processor.sub_processor.message,
            "Account upload method None not implemented",
        )
        self.assertFalse(account_file_upload_processor.pre_check(""))
        self.assertFalse(account_file_upload_processor.post_check(""))
        self.assertFalse(account_file_upload_processor.process(""))


class TestDKBAccountFileUploadManager(TestCase):
    def setUp(self):
        self.account_hub = AccountHubFactory()
        self.credit_institution_sat = CreditInstitutionStaticSatelliteFactory(
            account_upload_method="dkb",
        )
        self.account_hub.link_account_credit_institution.add(
            self.credit_institution_sat.hub_entity
        )
        self.upload_registry = FileUploadRegistryStaticSatelliteFactory()
        self.account_hub.link_account_file_upload_registry.add(
            self.upload_registry.hub_entity
        )

    def test_right_processor(self):
        account_file_upload_processor = AccountFileUploadProcessor(
            file_upload_registry_id=self.upload_registry.pk,
            **{"pk": self.account_hub.pk},
        )
        self.assertIsInstance(
            account_file_upload_processor.sub_processor, DkbFileUploadProcessor
        )


class TestOnvistaAccountFileUploadManagerDepot(TestCase):
    def setUp(self):
        self.account_hub = AccountHubFactory()
        self.credit_institution_sat = CreditInstitutionStaticSatelliteFactory(
            account_upload_method="onvis",
        )
        self.account_hub.link_account_credit_institution.add(
            self.credit_institution_sat.hub_entity
        )
        self.upload_registry = FileUploadRegistryStaticSatelliteFactory()
        self.account_hub.link_account_file_upload_registry.add(
            self.upload_registry.hub_entity
        )

    def test_right_processor(self):
        account_file_upload_processor = AccountFileUploadProcessor(
            file_upload_registry_id=self.upload_registry.pk,
            **{"pk": self.account_hub.pk},
        )
        self.assertIsInstance(
            account_file_upload_processor.sub_processor, OnvistaFileUploadProcessor
        )
