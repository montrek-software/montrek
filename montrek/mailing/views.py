from django.http import HttpResponseRedirect
from django.urls import reverse

from baseclasses.views import (
    MontrekCreateUpdateView,
    MontrekListView,
    MontrekDetailView,
)
from mailing.managers.mailing_manager import (
    MailingManager,
)
from mailing.managers.mailing_table_manager import (
    MailingTableManager,
    MailingDetailsManager,
)

from mailing.pages import MailingPage
from baseclasses.dataclasses.view_classes import ActionElement
from mailing.forms import MailingSendForm


# Create your views here.
#
class MailOverviewListView(MontrekListView):
    manager_class = MailingTableManager
    page_class = MailingPage
    title = "Mail Overview"
    tab = "tab_overview"

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

    def get_form(self, form_class=None):
        if "pk" in self.kwargs:
            initial = self.manager.get_object_from_pk_as_dict(self.kwargs["pk"])
        return self.form_class(repository=self.manager.repository, initial=initial)

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
    manager_class = MailingDetailsManager
    page_class = MailingPage
    title = "Mail Details"
    tab = "tab_mail_details"
