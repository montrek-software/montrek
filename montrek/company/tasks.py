from celery import shared_task
from company.managers.rgs import RgsFileProcessor


@shared_task
def process_rgs_file_task(
    file_path: str, session_data: dict, file_upload_registry_id: int
):
    # return RgsFileProcessor(session_data, file_upload_registry_id).process(file_path)
    return "hello world"
