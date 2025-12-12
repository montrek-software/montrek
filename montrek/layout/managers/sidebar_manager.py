from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from django.db.models import QuerySet
from django.template.loader import render_to_string
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManagerABC


@dataclass
class SidebarLinkTableElement(te.LinkTextTableElement):
    compare_url: str = field(default="")

    def is_active(self, value: Any, obj: Any) -> bool:
        url = self.get_url(obj)
        return url == self.compare_url


class SidebarManagerABC(MontrekTableManagerABC):
    group_field: str = "group_field not set"

    def link(self) -> SidebarLinkTableElement:
        raise NotImplementedError("Method 'link' has to be implemented")

    def get_full_table(self) -> QuerySet | dict:
        self.set_order_field()
        return self.repository.receive()

    def to_html(self):
        items = self.get_full_table()

        # Group sections by topic
        grouped_items = defaultdict(list)
        active_group = None
        link = self.link()
        for item in items:
            group = getattr(item, self.group_field)
            if link.is_active(None, item):
                active_group = group
            grouped_items[group].append(link.get_display_field(item))
        # Render using Django template
        html = render_to_string(
            "sidebar.html",
            {
                "grouped_items": dict(grouped_items),
                "active_group": active_group,
            },
        )

        return html
