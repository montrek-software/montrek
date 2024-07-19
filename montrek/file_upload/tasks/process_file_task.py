from montrek.celery_app import app as celery_app
from celery import Task


from mailing.managers.mailing_manager import MailingManager
from django.contrib.auth import get_user_model

from baseclasses.managers.montrek_manager import MontrekManager
from file_upload.managers.file_upload_manager import (
    FileUploadProcessorProtocol,
)
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepositoryABC,
)


class ProcessFileTaskBase(Task):
    def __init__(
        self,
        *args,
        file_upload_processor_class: FileUploadProcessorProtocol,
        file_upload_registry_repository_class: type[FileUploadRegistryRepositoryABC],
        **kwargs,
    ) -> None:
        super().__init__()
        self.file_upload_processor_class = file_upload_processor_class
        self.file_upload_registry_repository_class = (
            file_upload_registry_repository_class
        )
        celery_app.register_task(self)

    def run(
        self,
        *args,
        file_path: str,
        file_upload_registry_id: int,
        session_data: dict,
        **kwargs,
    ) -> str:
        # Arguments have to be serializable so we cannot pass repository,
        # processor objects from manager.
        registry_repo = self.file_upload_registry_repository_class(
            session_data=session_data
        )
        registry_obj = registry_repo.std_queryset().get(pk=file_upload_registry_id)
        processor = self.file_upload_processor_class(
            file_upload_registry_hub=registry_obj, session_data=session_data
        )
        result = processor.process(file_path)
        result = processor.post_check(file_path) if result else False
        user = get_user_model().objects.get(pk=session_data["user_id"])
        MailingManager(session_data=session_data).send_montrek_mail(
            user.email, "Backgroud File Upload Finished", processor.message
        )
        att_dict = registry_repo.object_to_dict(registry_obj)
        att_dict.update(
            {
                "upload_status": "processed" if result else "failed",
                "upload_message": processor.message,
            },
        )
        registry_obj = registry_repo.std_create_object(att_dict)
        return processor.message
