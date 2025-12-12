from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from django.db.models import QuerySet
from django.template.loader import render_to_string
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManagerABC


@dataclass
class SidebarLinkTabelElement(te.LinkTextTableElement):
    compare_url: str = field(default="")


class SidebarManagerABC(MontrekTableManagerABC):
    group_field: str = "group_field not set"
    sidebar_link_table_element_class: type[SidebarLinkTabelElement] = (
        SidebarLinkTabelElement
    )

    def get_link_table_element(self) -> SidebarLinkTabelElement:
        return self.sidebar_link_table_element_class(
            compare_url=self.compare_url(), **self.get_link_table_element_kwargs()
        )

    def get_link_table_element_kwargs(self) -> dict[str, Any]:
        raise NotImplementedError

    def compare_url(self) -> str:
        return ""

    def get_full_table(self) -> QuerySet | dict:
        self.set_order_field()
        return self.repository.receive()

    def to_html(self):
        items = self.get_full_table()

        # Group sections by topic
        grouped_items = defaultdict(list)
        compare_url = self.compare_url()
        active_group = None
        link_table_element = self.get_link_table_element()
        for item in items:
            url_kwargs = link_table_element._get_url_kwargs(item)
            linked_url = link_table_element._get_url(item, url_kwargs)
            active = linked_url == compare_url
            group = getattr(item, self.group_field)
            item_link = link_table_element.get_display_field(item)
            if active:
                active_group = group
            # TODO: rewrite this such that the hover text is passed to the item and it works with a template
            grouped_items[group].append(item_link.display_value)
        # Render using Django template
        html = render_to_string(
            "sidebar.html",
            {
                "grouped_items": dict(grouped_items),
                "active_group": active_group,
            },
        )

        return html
