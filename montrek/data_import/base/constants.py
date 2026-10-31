from process_pipeline.constants import (
    RegistryStatusDataClass,
    RegistryStatusTextChoices,
)
from reporting.core.reporting_colors import ReportingColors


class ImportStatus(RegistryStatusTextChoices):
    PENDING = RegistryStatusDataClass("pending", ReportingColors.BLUE, is_active=True)
    UPLOADED = RegistryStatusDataClass("uploaded", ReportingColors.DARK_GREEN)
    IN_PROGRESS = RegistryStatusDataClass(
        "in_progress", ReportingColors.YELLOW, is_active=True
    )
    PROCESSED = RegistryStatusDataClass("processed", ReportingColors.DARK_GREEN)
    FAILED = RegistryStatusDataClass("failed", ReportingColors.RED)
