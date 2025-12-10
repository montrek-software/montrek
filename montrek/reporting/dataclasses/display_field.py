from dataclasses import dataclass


@dataclass
class DisplayField:
    name: str
    display_value: str
    style_attrs_str: str
    td_classes_str: str
