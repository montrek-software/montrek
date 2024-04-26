from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

from baseclasses.views import (
    MontrekCreateUpdateView,
    MontrekListView,
    MontrekDetailView,
)
from reporting.dataclasses import table_elements as te
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
            te.LinkTableElement(
                name="View",
                url="mail_detail",
                kwargs={"pk": "id"},
                hover_text="View Details",
                icon="chevron-right",
            ),
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
        mail_data = form.cleaned_data
        self.manager.send_montrek_mail(
            recipients=mail_data["mail_recipients"],
            subject=mail_data["mail_subject"],
            message=mail_data["mail_message"],
        )
        self.show_messages()
        return HttpResponseRedirect(self.get_success_url())


class MailDetailView(MontrekDetailView):
    manager_class = MailingManager
    page_class = MailingPage
    title = "Mail Details"
    tab = "tab_mail_details"

    @property
    def elements(self) -> list[te.TableElement]:
        return [
            te.StringTableElement(name="Subject", attr="mail_subject"),
            te.StringTableElement(name="Recipients", attr="mail_recipients"),
            te.StringTableElement(name="State", attr="mail_state"),
            te.StringTableElement(name="Message", attr="mail_message"),
            te.StringTableElement(name="Comment", attr="mail_comment"),
        ]
