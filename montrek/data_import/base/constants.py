from process_pipeline.constants import (
    RegistryStatusDataClass,
    RegistryStatusTextChoices,
)


class ImportStatus(RegistryStatusTextChoices):
    PENDING = RegistryStatusDataClass("pending")
    UPLOADED = RegistryStatusDataClass("uploaded")
    IN_PROGRESS = RegistryStatusDataClass("in_progress")
    PROCESSED = RegistryStatusDataClass("processed")
    FAILED = RegistryStatusDataClass("failed")
