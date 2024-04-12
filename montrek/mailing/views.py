from django.shortcuts import render

from baseclasses.views import MontrekListView
from baseclasses.dataclasses import table_elements as te
from mailing.managers.mailing_manager import MailingManager
from mailing.pages import MailingPage


# Create your views here.
#
class MailOverviewListView(MontrekListView):
    manager_class = MailingManager
    page_class = MailingPage
    title = "Mail Overview"
    tab = "tab_overview"

    @property
    def elements(self) -> list[te.TableElement]:
        return [
            te.StringTableElement(name="Subject", attr="mail_subject"),
            te.StringTableElement(name="Recipients", attr="mail_recipients"),
            te.StringTableElement(name="State", attr="mail_state"),
        ]
