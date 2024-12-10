from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class SCompanyPage(MontrekPage):
    page_title = "SCompany"

    def get_tabs(self):
        return (
            TabElement(
                name="SCompany",
                link=reverse("scompany_list"),
                html_id="tab_scompany_list",
                active="active",
            ),
        )
