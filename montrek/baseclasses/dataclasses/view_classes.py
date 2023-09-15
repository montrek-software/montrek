from typing import List
from dataclasses import dataclass

@dataclass
class ActionElement:
    icon: str
    link: str
    action_id: str

@dataclass
class TabElement:
    name: str
    link: str
    html_id: str 
    #actions: List[ActionElement]
    active: str = ""

