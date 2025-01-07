from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekDetailsPage, MontrekPage
from showcase.repositories.scompany_repositories import SCompanyRepository


class SCompanyPage(MontrekPage):
    page_title = "Company"

    def get_tabs(self):
        return (
            TabElement(
                name="Company",
                link=reverse("scompany_list"),
                html_id="tab_scompany_list",
                active="active",
            ),
        )


class SCompanyDetailsPage(MontrekDetailsPage):
    repository_class = SCompanyRepository
    title_field = "company_name"

    def get_tabs(self):
        return (
            TabElement(
                name="Company",
                link=reverse("scompany_details", args=[self.obj.id]),
                html_id="tab_scompany_details",
            ),
        )
