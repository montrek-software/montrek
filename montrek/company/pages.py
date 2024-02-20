from django.urls import reverse
from company.repositories.company_repository import CompanyRepository
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage


class CompanyOverviewPage(MontrekPage):
    page_title = "Countries"

    def get_tabs(self):
        action_new_company = ActionElement(
           icon="plus",
           link=reverse("company_create"),
           action_id="id_create_company",
           hover_text="Create company",
        )
        overview_tab = TabElement(
           name="Company List",
           link=reverse("company"),
           html_id="tab_company_list",
           active="active",
           actions=(action_new_company,),
        )
        return (overview_tab,)


class CompanyPage(MontrekPage):
   def __init__(self, **kwargs):
       super().__init__(**kwargs)
       if "pk" not in kwargs:
           raise ValueError("CompanyPage needs pk specified in url!")
       self.obj = CompanyRepository().std_queryset().get(pk=kwargs["pk"])
       self.page_title = self.obj.company_name

   def get_tabs(self):
       action_back = ActionElement(
           icon="arrow-left",
           link=reverse("company"),
           action_id="back_to_overview",
           hover_text="Back to Overview",
       )
       action_update_company = ActionElement(
           icon="pencil",
           link=reverse("company_update", kwargs={"pk": self.obj.id}),
           action_id="id_update_company",
           hover_text="Update Company",
       )
       details_tab = TabElement(
           name="Details",
           link=reverse("company_details", args=[self.obj.id]),
           html_id="tab_details",
           actions=(action_back, action_update_company),
       )
       return [details_tab]
