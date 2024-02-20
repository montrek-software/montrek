from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage
from montrek_example.repositories.hub_a_repository import HubARepository


class MontrekExampleAAppPage(MontrekPage):
    page_title = "Montrek Example A"

    def get_tabs(self):
        action_new_example_a = ActionElement(
            icon="plus",
            link=reverse("montrek_example_a_create"),
            action_id="id_new_example_a",
            hover_text="Add new A Example",
        )
        overview_tab = TabElement(
            name="Example A List",
            link=reverse("montrek_example_a_list"),
            html_id="tab_example_a_list",
            active="active",
            actions=(action_new_example_a,),
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
        action_back = ActionElement(
            icon="arrow-left",
            link=reverse("montrek_example_a_list"),
            action_id="back_to_overview",
            hover_text="Back to Overview",
        )
        action_update_example_a = ActionElement(
            icon="pencil",
            link=reverse("montrek_example_a_update", kwargs={"pk": self.obj.id}),
            action_id="id_update_example_a",
            hover_text="Update ExampleA",
        )
        details_tab = TabElement(
            name="Details",
            link=reverse("montrek_example_a_details", args=[self.obj.id]),
            html_id="tab_details",
            actions=(action_back, action_update_example_a),
        )
        history_tab = TabElement(
            name="History",
            link=reverse("montrek_example_a_history", args=[self.obj.id]),
            html_id="tab_history",
            actions=(action_back,),
        )
        return [details_tab, history_tab]


class MontrekExampleBAppPage(MontrekPage):
    page_title = "Montrek Example B"

    def get_tabs(self):
        action_new_example_b = ActionElement(
            icon="plus",
            link=reverse("montrek_example_b_create"),
            action_id="id_new_example_b",
            hover_text="Add new B Example",
        )
        overview_tab = TabElement(
            name="Example B List",
            link=reverse("montrek_example_b_list"),
            html_id="tab_example_b_list",
            active="active",
            actions=(action_new_example_b,),
        )
        return (overview_tab,)
