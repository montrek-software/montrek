from django.urls import reverse
from country.repositories.country_repository import CountryRepository
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage


class CountryOverviewPage(MontrekPage):
    page_title = "Countries"

    def get_tabs(self):
        action_new_country = ActionElement(
           icon="plus",
           link=reverse("country_create"),
           action_id="id_create_country",
           hover_text="Create country",
        )
        overview_tab = TabElement(
           name="Country List",
           link=reverse("country"),
           html_id="tab_country_list",
           active="active",
           actions=(action_new_country,),
        )
        return (overview_tab,)


class CountryPage(MontrekPage):
   def __init__(self, **kwargs):
       super().__init__(**kwargs)
       if "pk" not in kwargs:
           raise ValueError("CountryPage needs pk specified in url!")
       self.obj = CountryRepository().std_queryset().get(pk=kwargs["pk"])
       self.page_title = self.obj.country_name

   def get_tabs(self):
       action_back = ActionElement(
           icon="arrow-left",
           link=reverse("country"),
           action_id="back_to_overview",
           hover_text="Back to Overview",
       )
       action_update_country = ActionElement(
           icon="pencil",
           link=reverse("country_update", kwargs={"pk": self.obj.id}),
           action_id="id_update_country",
           hover_text="Update Country",
       )
       details_tab = TabElement(
           name="Details",
           link=reverse("country_details", args=[self.obj.id]),
           html_id="tab_details",
           actions=(action_back, action_update_country),
       )
       return [details_tab]
