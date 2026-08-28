from process_pipeline.constants import (
    RegistryStatusDataClass,
    RegistryStatusTextChoices,
)
from reporting.core.reporting_colors import ReportingColors


class UploadStatus(RegistryStatusTextChoices):
    PENDING = RegistryStatusDataClass("pending", ReportingColors.BLUE)
    UPLOADED = RegistryStatusDataClass("uploaded", ReportingColors.DARK_GREEN)
    IN_PROGRESS = RegistryStatusDataClass("in_progress", ReportingColors.YELLOW)
    PROCESSED = RegistryStatusDataClass("processed", ReportingColors.DARK_GREEN)
    FAILED = RegistryStatusDataClass("failed", ReportingColors.RED)
    REVOKED = RegistryStatusDataClass("revoked", ReportingColors.RED)
