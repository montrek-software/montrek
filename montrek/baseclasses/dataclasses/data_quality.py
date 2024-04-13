from dataclasses import dataclass
from enum import Enum
from reporting.core.reporting_colors import ReportingColors


@dataclass
class DataQualityStatus:
    level: str
    color: str
    sort_order: int


class DataQualityStatusEnum(Enum):
    ERROR = DataQualityStatus("error", ReportingColors.RED, 0)
    WARNING = DataQualityStatus("warning", ReportingColors.YELLOW, 1)
    OK = DataQualityStatus("ok", ReportingColors.BRIGHTER_GREEN, 2)

    @classmethod
    def _get_by_level(cls, level):
        for status in cls:
            if status.value.level == level:
                return status

    @classmethod
    def get_color_by_level(cls, level):
        return cls._get_by_level(level).value.color

    @classmethod
    def get_sort_order_by_level(cls, level):
        return cls._get_by_level(level).value.sort_order
