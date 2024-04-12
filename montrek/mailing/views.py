from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from baseclasses.views import MontrekCreateUpdateView, MontrekListView
from baseclasses.dataclasses import table_elements as te
from mailing.managers.mailing_manager import MailingManager
from mailing.pages import MailingPage
from baseclasses.dataclasses.view_classes import ActionElement
from mailing.forms import MailingSendForm


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

    @property
    def actions(self) -> tuple[ActionElement]:
        action_send_mail = ActionElement(
            icon="envelope",
            link=reverse("send_mail"),
            action_id="id_send_mail",
            hover_text="Send Mail",
        )
        return (action_send_mail,)


class SendMailView(MontrekCreateUpdateView):
    manager_class = MailingManager
    page_class = MailingPage
    title = "Send mail"
    tab = "tab_send_mail"
    form_class = MailingSendForm
    success_url = "mailing"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = "Send Mail"
        return context

    def form_valid(self, form):
        self.manager.send_mail(form.cleaned_data)
        return HttpResponseRedirect(self.get_success_url())
