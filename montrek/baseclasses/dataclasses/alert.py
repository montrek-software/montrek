from dataclasses import dataclass
from enum import Enum

from reporting.core.reporting_colors import Color, ReportingColors


@dataclass
class Alert:
    description: str
    color: Color
    sort_order: int


class AlertEnum(Enum):
    ERROR = Alert("error", ReportingColors.RED, -2)
    WARNING = Alert("warning", ReportingColors.YELLOW, -1)
    OK = Alert("ok", ReportingColors.BRIGHTER_GREEN, 0)
    UNKNOWN = Alert("unknonw", ReportingColors.BLACK, -3)

    @classmethod
    def get_by_description(cls, description) -> Alert:
        for alert in cls:
            if alert.value.description == description:
                return alert.value
        return cls.UNKNOWN.value
