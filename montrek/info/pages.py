from django.urls import reverse
from baseclasses.pages import MontrekPage
from baseclasses.dataclasses.view_classes import TabElement


class InfoPage(MontrekPage):
    page_title = "Montrek Infos"

    def get_tabs(self) -> tuple[TabElement]:
        info_tab = TabElement(
            name="Versions",
            link=reverse("info"),
            html_id="id_info",
        )
        return (info_tab,)
