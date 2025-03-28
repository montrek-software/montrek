from dataclasses import dataclass


@dataclass
class LinkModel:
    # Dataclass for links shown in montrek frontend
    href: str
    title: str
