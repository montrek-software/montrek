from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class FieldMapPage(MontrekPage):
    page_title = "Field Map"

    def get_tabs(self):
        overview_tab = TabElement(
            name="Field Map List",
            link=reverse("montrek_example_field_map_list"),
            html_id="tab_field_map_list",
            active="active",
        )
        return (overview_tab,)
