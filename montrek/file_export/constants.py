from process_pipeline.constants import (
    RegistryStatusDataClass,
    RegistryStatusTextChoices,
)
from reporting.core.reporting_colors import ReportingColors


class ExportStatus(RegistryStatusTextChoices):
    PENDING = RegistryStatusDataClass("pending", ReportingColors.BLUE)
    IN_PROGRESS = RegistryStatusDataClass("in_progress", ReportingColors.YELLOW)
    PROCESSED = RegistryStatusDataClass("processed", ReportingColors.DARK_GREEN)
    FAILED = RegistryStatusDataClass("failed", ReportingColors.RED)
