from dataclasses import dataclass
from enum import Enum
from reporting.core.reporting_colors import ReportingColors


@dataclass
class DataQualityStatus:
    description: str
    color: str
    sort_order: int


class DataQualityStatusEnum(Enum):
    ERROR = DataQualityStatus("error", ReportingColors.RED, -2)
    WARNING = DataQualityStatus("warning", ReportingColors.YELLOW, -1)
    OK = DataQualityStatus("ok", ReportingColors.BRIGHTER_GREEN, 0)

    @classmethod
    def get_by_description(cls, description) -> DataQualityStatus:
        for status in cls:
            if status.value.description == description:
                return status.value
        raise ValueError(f"Invalid description: {description}")
