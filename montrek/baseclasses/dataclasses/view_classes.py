from typing import List
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
    actions: List[ActionElement]
    active: str = ""

@dataclass
class TableElement:
    name: str

@dataclass
class StringTableElement(TableElement):
    attr: str

@dataclass
class LinkTableElement(TableElement):
    url: str
    kwargs: dict
    icon: str
    hover_text: str
