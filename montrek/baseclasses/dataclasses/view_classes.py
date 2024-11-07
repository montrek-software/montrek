from dataclasses import dataclass


@dataclass
class ActionElement:
    icon: str
    link: str
    action_id: str
    hover_text: str


@dataclass
class BackActionElement(ActionElement):
    def __init__(self, link: str):
        self.icon = "arrow-left"
        self.link = link
        self.action_id = "id_back_action"
        self.hover_text = "Go Back"


@dataclass
class TabElement:
    name: str
    link: str
    html_id: str
    active: str = ""
