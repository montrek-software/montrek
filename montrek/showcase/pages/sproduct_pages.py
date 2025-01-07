from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekDetailsPage, MontrekPage
from showcase.repositories.sproduct_repositories import SProductRepository


class SProductPage(MontrekPage):
    page_title = "Investment Overview"

    def get_tabs(self):
        return (
            TabElement(
                name="Product",
                link=reverse("showcase"),
                html_id="tab_sproduct_list",
                active="active",
            ),
        )


class SProductDetailsPage(MontrekDetailsPage):
    repository_class = SProductRepository
    title_field = "product_name"

    def get_tabs(self):
        return (
            TabElement(
                name="Details",
                link=reverse("sproduct_details", args=[self.obj.id]),
                html_id="tab_sproduct_details",
                active="active",
            ),
            TabElement(
                name="Transactions",
                link=reverse("sproduct_stransaction_list", args=[self.obj.id]),
                html_id="tab_sproduct_stransaction_list",
                active="",
            ),
            TabElement(
                name="Positions",
                link=reverse("sproduct_sposition_list", args=[self.obj.id]),
                html_id="tab_sproduct_sposition_list",
                active="",
            ),
            TabElement(
                name="Report",
                link=reverse("sproduct_report", args=[self.obj.id]),
                html_id="tab_sproduct_report",
                active="",
            ),
        )
