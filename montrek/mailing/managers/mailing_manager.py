from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from baseclasses.managers.montrek_manager import MontrekManager
from mailing.repositories.mailing_repository import MailingRepository
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageInfo,
    MontrekMessageError,
)
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from smtplib import SMTPException


class MailingTableManager(MontrekTableManager):
    repository_class = MailingRepository

    @property
    def table_elements(self) -> list[te.TableElement]:
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


class MailingDetailsManager(MontrekDetailsManager):
    repository_class = MailingRepository

    @property
    def table_elements(self) -> list[te.TableElement]:
        return [
            te.StringTableElement(name="Subject", attr="mail_subject"),
            te.StringTableElement(name="Recipients", attr="mail_recipients"),
            te.StringTableElement(name="State", attr="mail_state"),
            te.StringTableElement(name="Message", attr="mail_message"),
            te.StringTableElement(name="Comment", attr="mail_comment"),
        ]


class MailingManager(MontrekManager):
    repository_class = MailingRepository

    @property
    def template_path(self):
        return settings.EMAIL_TEMPLATE

    def send_montrek_mail(
        self,
        recipients: str,
        subject: str,
        message: str,
        additional_parms: dict = {},
        attachments: list | None = None,
    ):
        recipient_list = recipients.replace(" ", "").split(",")
        mail_params: dict = {
            "mail_subject": subject,
            "mail_recipients": recipients,
            "mail_message": message,
            "mail_state": "Pending",
        }
        mail_hub = self.repository.std_create_object(mail_params)
        body = self.get_mail_body(message, additional_parms)

        try:
            email = EmailMessage(
                subject,
                body,
                settings.EMAIL_BACKEND,
                recipient_list,
                attachments=attachments,
            )
            email.content_subtype = "html"
            email.send()
            mail_success_params = {
                "mail_state": "Sent",
                "mail_comment": "Successfully send",
                "hub_entity_id": mail_hub.id,
            }
            self.repository.std_create_object(mail_success_params)
            self.messages.append(
                MontrekMessageInfo(message=f"Mail successfully sent to {recipients}")
            )
        except SMTPException as e:
            mail_fail_params = {
                "mail_state": "Failed",
                "mail_comment": str(e),
                "hub_entity_id": mail_hub.id,
            }
            self.repository.std_create_object(mail_fail_params)
            self.messages.append(
                MontrekMessageError(message=f"Mail failed to send to {recipients}")
            )

    def send_montrek_mail_to_user(
        self, subject: str, message: str, additional_parms: dict = {}
    ) -> None:
        user_id = self.session_data["user_id"]
        user = get_user_model().objects.get(pk=user_id)
        self.send_montrek_mail(user.email, subject, message, additional_parms)

    def get_mail_body(
        self,
        message: str,
        additional_parms: dict,
    ):
        return render_to_string(
            self.template_path, self.get_context_data(message, additional_parms)
        )

    def get_context_data(self, message: str, additional_parms: dict):
        return {"message": message, **additional_parms}
