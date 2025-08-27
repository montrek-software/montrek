from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage
from django.urls import reverse


class InfoPage(MontrekPage):
    page_title = "Montrek Infos"

    def get_tabs(self) -> tuple[TabElement]:
        db_structure_tab = TabElement(
            name="DB Structure",
            link=reverse("db_structure"),
            html_id="id_db_structure",
        )
        info_tab = TabElement(
            name="Versions",
            link=reverse("info"),
            html_id="id_info",
        )
        admin_tab = TabElement(
            name="Admin",
            link=reverse("admin"),
            html_id="id_admin",
        )
        return (db_structure_tab, info_tab, admin_tab)
