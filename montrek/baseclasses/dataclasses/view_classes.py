from dataclasses import dataclass

@dataclass
class TabElement:
    name: str
    link: str
    html_id: str 
    active: str = ""

@dataclass
class ActionElement:
    icon: str
    link: str
    action_id: str
