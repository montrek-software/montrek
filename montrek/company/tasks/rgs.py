import dataclasses

from typing import Any
from django.contrib.auth import get_user_model
from django.conf import settings
from celery import shared_task
from company.managers.rgs import RgsFileProcessor

from django.core.mail import send_mail


@shared_task
def process_rgs_file_task(
    file_path: str, session_data: dict, file_upload_registry_id: int
):
    processor = RgsFileProcessor(session_data, file_upload_registry_id)
    processor.process(file_path)
    user = get_user_model().objects.get(pk=session_data["user_id"])
    send_mail(
        "RGS File Upload Terminated",
        processor.message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )
    return processor.message
