from process_pipeline.constants import (
    RegistryStatusDataClass,
    RegistryStatusTextChoices,
)


class ExportStatus(RegistryStatusTextChoices):
    PENDING = RegistryStatusDataClass("pending")
    IN_PROGRESS = RegistryStatusDataClass("in_progress")
    PROCESSED = RegistryStatusDataClass("processed")
    FAILED = RegistryStatusDataClass("failed")
