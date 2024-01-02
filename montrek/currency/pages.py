from django.urls import reverse

from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage
from currency.repositories.currency_repository import CurrencyRepository


class CurrencyAppPage(MontrekPage):
    page_title = "Currencies"

    def get_tabs(self):
        action_new_currency = ActionElement(
            icon="plus",
            link=reverse("currency_create"),
            action_id="id_create_currency",
            hover_text="Create Currency",
        )
        return [
            TabElement(
                html_id="tab_overview",
                name="Overview",
                link=reverse("currency"),
                actions=(action_new_currency,),
            ),
        ]


class CurrencyPage(MontrekPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "pk" not in kwargs:
            raise ValueError("CurrencyPage needs pk specified in url!")
        self.obj = CurrencyRepository().std_queryset().get(pk=kwargs["pk"])
        self.page_title = self.obj.ccy_name

    def get_tabs(self):
        action_back = ActionElement(
            icon="arrow-left",
            link=reverse("currency"),
            action_id="back_to_overview",
            hover_text="Back to Overview",
        )
        details_tab = TabElement(
            name="Details",
            link=reverse("currency_details", args=[self.obj.id]),
            html_id="tab_details",
            actions=(action_back,),
        )
        return [details_tab]
