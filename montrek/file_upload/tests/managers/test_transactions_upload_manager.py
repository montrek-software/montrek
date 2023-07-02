from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage

from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionStaticSatelliteFactory
from link_tables.tests.factories.link_tables_factories import AccountCreditInstitutionLinkFactory
from file_upload.tests.factories.file_upload_factories import FileUploadRegistryStaticSatelliteFactory
from file_upload.tests.factories.file_upload_factories import FileUploadFileStaticSatelliteFactory
from link_tables.tests.factories.link_tables_factories import FileUploadRegistryFileUploadFileLinkFactory
from link_tables.tests.factories.link_tables_factories import AccountFileUploadRegistryLinkFactory

from file_upload.managers.transactions_upload_manager import init_file_upload_registry
from file_upload.managers.transactions_upload_manager import upload_file_upload_registry
from file_upload.managers.transactions_upload_manager import upload_error_file_not_uploaded_registry
from file_upload.managers.transactions_upload_manager import upload_error_account_upload_method_none
from file_upload.managers.transactions_upload_manager import upload_transactions_to_account_manager

class TestTransactionsUploadManager(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.account_satellite = AccountStaticSatelliteFactory()
        cls.credit_institution_satellite = CreditInstitutionStaticSatelliteFactory()
        cls.account_credit_institution_link = AccountCreditInstitutionLinkFactory(
            from_hub=cls.account_satellite.hub_entity,
            to_hub=cls.credit_institution_satellite.hub_entity
        )
        # Create a file to upload
        txt_file_content = b'Test file content'
        cls.txt_file = SimpleUploadedFile('test_file.txt', txt_file_content)
        cls.file_registry_sat_factory = FileUploadRegistryStaticSatelliteFactory(
            file_name=cls.txt_file.name
        )
        cls.file_file_sat_factory = FileUploadFileStaticSatelliteFactory()
        file_registry_file_link_factory = FileUploadRegistryFileUploadFileLinkFactory(
            from_hub=cls.file_registry_sat_factory.hub_entity,
            to_hub=cls.file_file_sat_factory.hub_entity
        )
        AccountFileUploadRegistryLinkFactory(
            from_hub=cls.account_satellite.hub_entity,
            to_hub=cls.file_registry_sat_factory.hub_entity
        )

    def tearDown(self):
        if default_storage.exists('uploads/test_file.txt'):
            default_storage.delete('uploads/test_file.txt')

    def test_init_file_upload_registry(self):
        file_registry_sat = init_file_upload_registry(
            self.account_satellite.hub_entity.id,
            self.txt_file,
        )
        self.assertEqual(file_registry_sat.upload_status, 'pending')
        self.assertEqual(file_registry_sat.file_name, self.txt_file.name)

    def test_upload_transactions_to_account_manager(self):
        not_uploaded_file_reg = upload_transactions_to_account_manager(self.file_registry_sat_factory)
        self.assertEqual(not_uploaded_file_reg.upload_status, 'failed')
        not_uploaded_file_reg.upload_status = 'uploaded'
        not_uploaded_file_reg.save()
        no_upload_method = upload_transactions_to_account_manager(not_uploaded_file_reg)
        self.assertEqual(no_upload_method.upload_status, 'failed')
        self.credit_institution_satellite.account_upload_method = 'test'
        self.credit_institution_satellite.save()
        uploaded = upload_transactions_to_account_manager(not_uploaded_file_reg)
        self.assertEqual(uploaded.upload_status, 'processed')



    def test_upload_error_file_not_uploaded_registry(self):
        file_registry_sat_failed = upload_error_file_not_uploaded_registry(
            self.file_registry_sat_factory
        )
        self.assertEqual(file_registry_sat_failed.upload_status, 'failed')
        self.assertEqual(file_registry_sat_failed.upload_message, 'File test_file.txt has not been not uploaded')

    def test_upload_error_account_upload_method_none(self):
        file_registry_sat_failed = upload_error_account_upload_method_none(
            self.file_registry_sat_factory,
            self.credit_institution_satellite
        )
        self.assertEqual(file_registry_sat_failed.upload_status, 'failed')
        self.assertEqual(file_registry_sat_failed.upload_message, 
                         f'Credit Institution {self.credit_institution_satellite.credit_institution_name} provides no upload method')
