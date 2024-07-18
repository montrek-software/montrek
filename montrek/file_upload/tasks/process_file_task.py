from celery import Task
from montrek.celery_app import app


from mailing.managers.mailing_manager import MailingManager
from django.contrib.auth import get_user_model

from baseclasses.managers.montrek_manager import MontrekManager
from file_upload.managers.file_upload_manager import (
    FileUploadProcessorProtocol,
)


class ProcessFileTaskBase(Task):
    file_upload_processor_class: type[FileUploadProcessorProtocol]
    file_registry_manager_class: type[MontrekManager]

    def run(
        self,
        *args,
        file_path: str,
        file_upload_registry_id: int,
        session_data: dict,
        **kwargs,
    ) -> str:
        # Arguments have to be serializable, so we cannot pass in the processor directly
        # from the manager.
        registry_manager = self.file_registry_manager_class(session_data)
        registry_repo = registry_manager.repository
        registry = registry_repo.std_queryset().get(pk=file_upload_registry_id)
        processor = self.file_upload_processor_class(
            file_upload_registry_hub=registry, session_data=session_data
        )
        result = processor.process(file_path)
        user = get_user_model().objects.get(pk=session_data["user_id"])
        MailingManager(session_data=session_data).send_montrek_mail(
            user.email, "Backgroud File Upload Finished", processor.message
        )
        att_dict = registry_manager.repository.object_to_dict(registry)
        att_dict.update(
            {
                "upload_status": "processed" if result else "failed",
                "upload_message": processor.message,
            },
        )
        registry = registry_manager.repository.std_create_object(att_dict)
        return processor.message


# for subclass in ProcessFileTaskBase.__subclasses__():
#     app.register_task(subclass)
