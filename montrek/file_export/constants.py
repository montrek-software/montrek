from process_pipeline.constants import RegistryStatusTextChoices


class ExportStatus(RegistryStatusTextChoices):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PROCESSED = "processed"
    FAILED = "failed"
