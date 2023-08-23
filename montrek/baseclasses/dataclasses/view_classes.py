from dataclasses import dataclass

@dataclass
class TabElement:
    # TODO: Move to baseclasses
    name: str
    link: str
    active: bool = False

@dataclass
class ActionElement:
    icon: str
    link: str
    action_id: str
