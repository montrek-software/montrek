from dataclasses import dataclass, field
from baseclasses.utils import ChoicesEnum

from reporting.core.reporting_colors import Color, ReportingColors


@dataclass
class RegistryStatusDataClass:
    label: str
    color: Color = field(default_factory=lambda: ReportingColors.BLUE)


class RegistryStatusTextChoices(ChoicesEnum):
    @classmethod
    def to_list(cls) -> list[tuple[str, str]]:
        return [
            (member.value.label, member.value.label.replace("_", " ").title())
            for member in cls
        ]

    @classmethod
    def label_colors(cls) -> dict[str, Color]:
        return {member.value.label: member.value.color for member in cls}
