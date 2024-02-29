from typing import Tuple
from dataclasses import dataclass


@dataclass
class ActionElement:
    icon: str
    link: str
    action_id: str
    hover_text: str


@dataclass
class TabElement:
    name: str
    link: str
    html_id: str
    actions: Tuple[ActionElement]
    active: str = ""
