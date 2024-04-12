from django.urls import reverse
from baseclasses.pages import MontrekPage
from baseclasses.dataclasses.view_classes import TabElement


class MailingPage(MontrekPage):
    page_title = "Mailing"

    def get_tabs(self):
        overview_tab = TabElement(
            name="Mails Overview",
            link=reverse("mailing"),
            html_id="tab_overview",
            active="active",
        )
        return (overview_tab,)
