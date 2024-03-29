from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage
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
        return (overview_tab,)


class ExampleAPage(MontrekPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "pk" not in kwargs:
            raise ValueError("ExampleAPage needs pk specified in url!")
        self.obj = HubARepository().std_queryset().get(pk=kwargs["pk"])
        self.page_title = self.obj.field_a1_str

    def get_tabs(self):
        details_tab = TabElement(
            name="Details",
            link=reverse("montrek_example_a_details", args=[self.obj.id]),
            html_id="tab_details",
        )
        history_tab = TabElement(
            name="History",
            link=reverse("montrek_example_a_history", args=[self.obj.id]),
            html_id="tab_history",
        )
        return [details_tab, history_tab]


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
