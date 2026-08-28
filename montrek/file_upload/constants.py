from process_pipeline.constants import RegistryStatusTextChoices


class UploadStatus(RegistryStatusTextChoices):
    PENDING = "pending"
    UPLOADED = "uploaded"
    IN_PROGRESS = "in_progress"
    PROCESSED = "processed"
    FAILED = "failed"
    REVOKED = "revoked"
