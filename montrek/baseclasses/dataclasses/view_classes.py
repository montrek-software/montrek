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
        kwargs: dict = {},
        action_id: str = "",
        hover_text: str = "",
    ):
        self.link = reverse(url_name, kwargs=kwargs)
        self.action_id = action_id or f"id_action_{url_name}"
        self.hover_text = hover_text or f"Go to {url_name.replace('_', ' ').title()}"


@dataclass(init=False)
class BackActionElement(StandardActionElementBase):
    icon = "arrow-left"


@dataclass(init=False)
class UploadActionElement(StandardActionElementBase):
    icon = "upload"


@dataclass(init=False)
class SettingsActionElement(StandardActionElementBase):
    icon = "cog"


@dataclass(init=False)
class CreateActionElement(StandardActionElementBase):
    icon = "plus"


@dataclass(init=False)
class RegistryActionElement(StandardActionElementBase):
    icon = "inbox"


@dataclass(init=False)
class ListActionElement(StandardActionElementBase):
    icon = "align-justify"


@dataclass
class TabElement:
    name: str
    link: str
    html_id: str
    active: str = ""
