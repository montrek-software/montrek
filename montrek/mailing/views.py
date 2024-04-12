from django.shortcuts import render

from baseclasses.views import MontrekListView
from mailing.managers.mailing_manager import MailingManager
from mailing.pages import MailingPage


# Create your views here.
#
class MailOverviewListView(MontrekListView):
    manager_class = MailingManager
    page_class = MailingPage
    title = "Mail Overview"
