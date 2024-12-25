from django.core import mail
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from file_upload.tests.mocks import (
    MockFileUploadManager,
    MockFileUploadManagerProcessorFail,
    MockFileUploadManagerProcessorPostCheckFail,
    MockFileUploadManagerProcessorPreCheckFail,
    MockFileUploadManagerSeq,
)
from montrek.celery_app import PARALLEL_QUEUE_NAME, SEQUENTIAL_QUEUE_NAME
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestFileUploadManager(TestCase):
    def setUp(self):
        self.test_file = SimpleUploadedFile(
            name="test_file.txt",
            content="test".encode("utf-8"),
            content_type="text/plain",
        )
        self.user = MontrekUserFactory()
        self.session_data = {"user_id": self.user.id}
        filter_data = {
            "request_path": "test_path",
            "filter": {
                "test_path": {
                    "value_date": {
                        "filter_value": "2024-01-01",
                        "filter_negate": False,
                    }
                }
            },
        }
        self.session_data.update(filter_data)

    def test_init_subclass(self):
        task = MockFileUploadManager.process_file_task
        self.assertEqual(
            task.name,
            f"file_upload.tests.mocks.MockFileUploadManager_process_file_task",
        )
        self.assertEqual(task.queue, PARALLEL_QUEUE_NAME)
        self.assertEqual(task.manager_class, MockFileUploadManager)
        task = MockFileUploadManagerSeq.process_file_task
        self.assertEqual(
            task.name,
            f"file_upload.tests.mocks.MockFileUploadManagerSeq_process_file_task",
        )
        self.assertEqual(task.queue, SEQUENTIAL_QUEUE_NAME)
        self.assertEqual(task.manager_class, MockFileUploadManagerSeq)

    def test_fum_register_file_in_db(self):
        manager = MockFileUploadManager(
            session_data=self.session_data,
        )
        manager.register_file_in_db(self.test_file)
        file_upload_registry_query = FileUploadRegistryRepository().receive()
        self.assertEqual(file_upload_registry_query.count(), 1)
        file_upload_registry = file_upload_registry_query.first()
        fname_pattern = r"test_file.*\.txt"
        self.assertRegex(file_upload_registry.file, fname_pattern)
        self.assertEqual(file_upload_registry.file_name, "test_file.txt")
        self.assertEqual(file_upload_registry.file_type, "txt")
        self.assertEqual(file_upload_registry.upload_status, "pending")
        self.assertEqual(file_upload_registry.upload_message, "Upload is pending")

    def test_fum_upload_success(self):
        fum = MockFileUploadManager(
            session_data=self.session_data,
        )
        for do_process_file_async in (False, True):
            fum.do_process_file_async = do_process_file_async
            fum.upload_and_process(self.test_file)
            file_upload_registry_query = FileUploadRegistryRepository().receive()
            self.assertEqual(file_upload_registry_query.count(), 1)
            file_upload_registry = file_upload_registry_query.first()
            self.assertEqual(file_upload_registry.upload_status, "processed")
            processor_message = (
                MockFileUploadManager.file_upload_processor_class.message
            )
            self.assertEqual(
                file_upload_registry.upload_message,
                processor_message,
            )

            if do_process_file_async:
                sent_email = mail.outbox[0]
                self.assertEqual(
                    sent_email.subject,
                    "Background file processing finished successfully.",
                )
                self.assertEqual(sent_email.to, [self.user.email])
                self.assertTrue(processor_message in sent_email.message().as_string())
            else:
                self.assertEqual(len(mail.outbox), 0)

    def test_fum_upload_failure(self):
        fum = MockFileUploadManagerProcessorFail(
            session_data=self.session_data,
        )
        for do_process_file_async in (False, True):
            fum.do_process_file_async = do_process_file_async
            fum.upload_and_process(self.test_file)
            file_upload_registry_query = FileUploadRegistryRepository().receive()
            self.assertEqual(file_upload_registry_query.count(), 1)
            file_upload_registry = file_upload_registry_query.first()
            self.assertEqual(file_upload_registry.upload_status, "failed")
            processor_message = (
                MockFileUploadManagerProcessorFail.file_upload_processor_class.message
            )
            self.assertEqual(
                file_upload_registry.upload_message,
                processor_message,
            )
            if do_process_file_async:
                sent_email = mail.outbox[0]
                self.assertEqual(
                    sent_email.subject,
                    "ERROR: Background file processing did not finish successfully!",
                )
                self.assertEqual(sent_email.to, [self.user.email])
                self.assertTrue(processor_message in sent_email.message().as_string())
            else:
                self.assertEqual(len(mail.outbox), 0)

    def test_fum_pre_check_fails(self):
        fum = MockFileUploadManagerProcessorPreCheckFail(
            session_data=self.session_data,
        )
        for do_process_file_async in (False, True):
            fum.do_process_file_async = do_process_file_async
            fum.upload_and_process(self.test_file)
            file_upload_registry_query = FileUploadRegistryRepository().receive()
            self.assertEqual(file_upload_registry_query.count(), 1)
            file_upload_registry = file_upload_registry_query.first()
            self.assertEqual(file_upload_registry.upload_status, "failed")
            self.assertEqual(
                file_upload_registry.upload_message,
                MockFileUploadManagerProcessorPreCheckFail.file_upload_processor_class.message,
            )

    def test_fum_post_check_fails(self):
        fum = MockFileUploadManagerProcessorPostCheckFail(
            session_data=self.session_data,
        )
        for do_process_file_async in (False, True):
            fum.do_process_file_async = do_process_file_async
            fum.upload_and_process(self.test_file)
            file_upload_registry_query = FileUploadRegistryRepository().receive()
            self.assertEqual(file_upload_registry_query.count(), 1)
            file_upload_registry = file_upload_registry_query.first()
            self.assertEqual(file_upload_registry.upload_status, "failed")
            self.assertEqual(
                file_upload_registry.upload_message,
                MockFileUploadManagerProcessorPostCheckFail.file_upload_processor_class.message,
            )
