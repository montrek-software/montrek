from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Self

from reporting.core.reporting_colors import Color, ReportingColors


@dataclass(frozen=True)
class MontrekType:
    name: str
    color: Color = ReportingColors.BLUE


class MontrekTypeEnum(Enum):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # __members__ includes aliases, so identical values are caught as well
        names = Counter(member.value.name for member in cls.__members__.values())
        duplicates = sorted(name for name, count in names.items() if count > 1)
        if duplicates:
            raise ValueError(
                f"{cls.__name__} has duplicate type names: {', '.join(duplicates)}"
            )

    @classmethod
    def to_list(cls) -> list[tuple[str, str]]:
        return [(member.value.name, member.value.name) for member in cls]

    @classmethod
    def to_color_dict(cls) -> dict[str, Color]:
        return {member.value.name: member.value.color for member in cls}

    @classmethod
    def from_name(cls, name: str) -> Self:
        for member in cls:
            if member.value.name == name:
                return member
        raise ValueError(f"{name!r} is not a valid {cls.__name__} name")
