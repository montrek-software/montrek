from dataclasses import dataclass

from django.urls import reverse


@dataclass
class ActionElement:
    icon: str
    link: str
    action_id: str
    hover_text: str


@dataclass
class StandardActionElementBase(ActionElement):
    icon = ""

    def __init__(
        self,
        url_name: str,
        action_id: str = "",
        hover_text: str = "",
    ):
        self.link = reverse(url_name)
        self.action_id = action_id or f"id_action_{url_name}"
        self.hover_text = hover_text or f"Go to {url_name.replace('_', ' ').title()}"


@dataclass(init=False)
class BackActionElement(StandardActionElementBase):
    icon = "arrow-left"


@dataclass(init=False)
class UploadActionElement(StandardActionElementBase):
    icon = "upload"


@dataclass
class TabElement:
    name: str
    link: str
    html_id: str
    active: str = ""
