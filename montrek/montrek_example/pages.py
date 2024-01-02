from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage

class MontrekExampleAAppPage(MontrekPage):
    page_title='Montrek Example A'

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

class MontrekExampleBAppPage(MontrekPage):
    page_title='Montrek Example B'

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
