from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage
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
            TabElement(
                name="Asset",
                link=reverse("sasset_list"),
                html_id="tab_sasset_list",
                active="",
            ),
        )


class SProductDetailsPage(MontrekPage):
    page_title = "Prodcut Details"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "pk" not in kwargs:
            raise ValueError(f"{self.__class__.__name__} needs pk specified in url!")
        self.obj = SProductRepository().receive().get(pk=kwargs["pk"])
        self.page_title = self.obj.product_name

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
        )
