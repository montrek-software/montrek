from mailing.repositories.mailing_repository import MailingRepository
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager


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
