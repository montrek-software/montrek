from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class CompanyPage(MontrekPage):
    page_title = "Company"

    def get_tabs(self):
        return (
            TabElement(
                name="Company",
                link=reverse("company_list"),
                html_id="tab_company_list",
                active="active",
            ),
        )
