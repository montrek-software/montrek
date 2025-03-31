from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekDetailsPage, MontrekPage
from montrek_example.managers.montrek_example_managers import (
    CompactHubAManager,
)
from montrek_example.repositories.hub_a_repository import HubARepository


class MontrekExampleAAppPage(MontrekPage):
    page_title = "Montrek Example A"

    def get_tabs(self):
        overview_tab = TabElement(
            name="Example A List",
            link=reverse("montrek_example_a_list"),
            html_id="tab_example_a_list",
            active="active",
        )
        file_upload_tab = TabElement(
            name="A1 Uploads",
            link=reverse("a1_view_uploads"),
            html_id="tab_uploads",
        )
        a1_field_map_tab = TabElement(
            name="A1 Field Map",
            link=reverse("montrek_example_a1_field_map_list"),
            html_id="tab_a1_field_map_list",
        )
        a2_api_upload_tab = TabElement(
            name="A2 API Uploads",
            link=reverse("hub_a_view_api_uploads"),
            html_id="tab_a2_uploads",
        )

        return (overview_tab, file_upload_tab, a1_field_map_tab, a2_api_upload_tab)


class ExampleAPage(MontrekDetailsPage):
    repository_class = HubARepository
    title_field = "field_a1_str"
    table_manager_class = CompactHubAManager

    def get_tabs(self):
        details_tab = TabElement(
            name="Details",
            link=reverse("montrek_example_a_details", args=[self.obj.id]),
            html_id="tab_details",
        )
        report_tab = TabElement(
            name="Report",
            link=reverse("montrek_example_a_report", args=[self.obj.id]),
            html_id="tab_report",
        )
        history_tab = TabElement(
            name="History",
            link=reverse("montrek_example_a_history", args=[self.obj.id]),
            html_id="tab_history",
        )
        return [details_tab, report_tab, history_tab]


class MontrekExampleBAppPage(MontrekPage):
    page_title = "Montrek Example B"

    def get_tabs(self):
        overview_tab = TabElement(
            name="Example B List",
            link=reverse("montrek_example_b_list"),
            html_id="tab_example_b_list",
            active="active",
        )
        return (overview_tab,)


class MontrekExampleCAppPage(MontrekPage):
    page_title = "Montrek Example C"

    def get_tabs(self):
        overview_tab = TabElement(
            name="Example C List",
            link=reverse("montrek_example_c_list"),
            html_id="tab_example_c_list",
            active="active",
        )
        return (overview_tab,)


class MontrekExampleDAppPage(MontrekPage):
    page_title = "Montrek Example D"

    def get_tabs(self):
        overview_tab = TabElement(
            name="Example D List",
            link=reverse("montrek_example_d_list"),
            html_id="tab_example_d_list",
            active="active",
        )
        return (overview_tab,)
