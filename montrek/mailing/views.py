from django.shortcuts import render

from baseclasses.views import MontrekListView
from mailing.managers.mailing_manager import MailingManager


# Create your views here.
#
class MailOverviewListView(MontrekListView):
    manager_class = MailingManager
