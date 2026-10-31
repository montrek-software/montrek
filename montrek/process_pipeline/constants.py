from dataclasses import dataclass, field
from baseclasses.utils import ChoicesEnum

from reporting.core.reporting_colors import Color, ReportingColors


@dataclass
class RegistryStatusDataClass:
    label: str
    color: Color = field(default_factory=lambda: ReportingColors.BLUE)
    # A background worker still has to move a run in this status on.
    is_active: bool = False


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

    @classmethod
    def active_labels(cls) -> tuple[str, ...]:
        return tuple(member.value.label for member in cls if member.value.is_active)
