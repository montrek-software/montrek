from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage

from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionStaticSatelliteFactory,
)
from link_tables.tests.factories.link_tables_factories import (
    AccountCreditInstitutionLinkFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from file_upload.tests.factories.file_upload_factories import (
    FileUploadFileStaticSatelliteFactory,
)
from link_tables.tests.factories.link_tables_factories import (
    FileUploadRegistryFileUploadFileLinkFactory,
)
from link_tables.tests.factories.link_tables_factories import (
    AccountFileUploadRegistryLinkFactory,
)

from file_upload.managers.transactions_upload_manager import _init_file_upload_registry
from file_upload.managers.transactions_upload_manager import (
    _upload_error_file_not_uploaded_registry,
)
from file_upload.managers.transactions_upload_manager import (
    _upload_error_account_upload_method_none,
)
from file_upload.managers.transactions_upload_manager import (
    _upload_transactions_to_account_manager,
)
from file_upload.managers.transactions_upload_manager import _upload_file_to_registry
from file_upload.managers.transactions_upload_manager import (
    process_upload_transaction_file,
)
from file_upload.repositories.file_upload_queries import (
    get_file_satellite_from_registry_satellite,
)


class TestTransactionsUploadManager(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.account_satellite = AccountStaticSatelliteFactory()
        cls.credit_institution_satellite = CreditInstitutionStaticSatelliteFactory()
        cls.account_credit_institution_link = AccountCreditInstitutionLinkFactory(
            from_hub=cls.account_satellite.hub_entity,
            to_hub=cls.credit_institution_satellite.hub_entity,
        )
        # Create a file to upload
        txt_file_content = b"Test file content"
        cls.txt_file = SimpleUploadedFile("test_file.txt", txt_file_content)
        cls.file_registry_sat_factory = FileUploadRegistryStaticSatelliteFactory(
            file_name=cls.txt_file.name
        )
        AccountFileUploadRegistryLinkFactory(
            from_hub=cls.account_satellite.hub_entity,
            to_hub=cls.file_registry_sat_factory.hub_entity,
        )
        dkb_csv_file_content = '"Kontonummer:";"DE96120300001008028225 / Girokonto";\n\n"Von:";"30.06.2023";\n"Bis:";"04.07.2023";\n"Kontostand vom 04.07.2023:";"792,15 EUR";\n\n"Buchungstag";"Wertstellung";"Buchungstext";"Auftraggeber / Begünstigter";"Verwendungszweck";"Kontonummer";"BLZ";"Betrag (EUR)";"Gläubiger-ID";"Mandatsreferenz";"Kundenreferenz";\n"05.07.2023";"05.07.2023";"ONLINE-UEBERWEISUNG";"FINANZAMT LIMBURG WEILBURG";"DATUM 04.07.2023, 20.17 UHR";"DE68500500000001000397";"HELADEFFXXX";"-1.348,50";"";"";"";'

        cls.dkb_csv_file = SimpleUploadedFile(
            "dkb_csv_file.csv", dkb_csv_file_content.encode("iso-8859-1")
        )

    def tearDown(self):
        if default_storage.exists("uploads/test_file.txt"):
            default_storage.delete("uploads/test_file.txt")

    def test_process_upload_transaction_file(self):
        test_registry = process_upload_transaction_file(
            self.account_satellite.hub_entity.id,
            self.txt_file,
        )
        self.assertEqual(test_registry.upload_status, "failed")
        self.assertEqual(
            test_registry.upload_message,
            f"Credit Institution {self.credit_institution_satellite.credit_institution_name} provides no upload method",
        )

    def test_process_upload_transaction_file_dkb(self):
        self.credit_institution_satellite.account_upload_method = "dkb"
        self.credit_institution_satellite.save()
        test_registry = process_upload_transaction_file(
            self.account_satellite.hub_entity.id,
            self.dkb_csv_file,
        )
        self.assertEqual(test_registry.upload_status, "processed")
        self.assertEqual(
            test_registry.upload_message,
            "DKB upload was successful! (uploaded 1 transactions)",
        )

    def test_init_file_upload_registry(self):
        file_registry_sat = _init_file_upload_registry(
            self.account_satellite.hub_entity.id,
            self.txt_file,
        )
        self.assertEqual(file_registry_sat.upload_status, "pending")
        self.assertEqual(file_registry_sat.file_name, self.txt_file.name)

    def test_upload_file_to_registry(self):
        file_registry_sat = _upload_file_to_registry(
            self.file_registry_sat_factory, self.txt_file
        )
        self.assertEqual(file_registry_sat.upload_status, "uploaded")
        self.assertEqual(
            file_registry_sat.upload_message, "File test_file.txt has been uploaded"
        )
        file_file_sat = get_file_satellite_from_registry_satellite(
            self.file_registry_sat_factory
        )
        self.assertEqual(file_file_sat.file.read(), b"Test file content")

    def test_upload_transactions_to_account_manager(self):
        not_uploaded_file_reg = _upload_transactions_to_account_manager(
            self.file_registry_sat_factory
        )
        self.assertEqual(not_uploaded_file_reg.upload_status, "failed")
        not_uploaded_file_reg.upload_status = "uploaded"
        not_uploaded_file_reg.save()
        no_upload_method = _upload_transactions_to_account_manager(
            not_uploaded_file_reg
        )
        self.assertEqual(no_upload_method.upload_status, "failed")
        self.credit_institution_satellite.account_upload_method = "test"
        self.credit_institution_satellite.save()
        uploaded = _upload_transactions_to_account_manager(not_uploaded_file_reg)
        self.assertEqual(uploaded.upload_status, "processed")
        self.assertEqual(uploaded.upload_message, "Test upload was successful!")
        self.credit_institution_satellite.account_upload_method = "nimpl"
        self.credit_institution_satellite.save()
        uploaded = _upload_transactions_to_account_manager(not_uploaded_file_reg)
        self.assertEqual(uploaded.upload_status, "failed")
        self.assertEqual(uploaded.upload_message, "Upload method nimpl not implemented")

    def test_upload_error_file_not_uploaded_registry(self):
        file_registry_sat_failed = _upload_error_file_not_uploaded_registry(
            self.file_registry_sat_factory
        )
        self.assertEqual(file_registry_sat_failed.upload_status, "failed")
        self.assertEqual(
            file_registry_sat_failed.upload_message,
            "File test_file.txt has not been not uploaded",
        )

    def test_upload_error_account_upload_method_none(self):
        file_registry_sat_failed = _upload_error_account_upload_method_none(
            self.file_registry_sat_factory, self.credit_institution_satellite
        )
        self.assertEqual(file_registry_sat_failed.upload_status, "failed")
        self.assertEqual(
            file_registry_sat_failed.upload_message,
            f"Credit Institution {self.credit_institution_satellite.credit_institution_name} provides no upload method",
        )
