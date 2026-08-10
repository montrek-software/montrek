"""Shared table columns for registries of pipeline runs.

Uploads and exports show the same thing — what ran, how it went, and what came
out of it — so the column building blocks live here. Subclasses name the status
and message fields and assemble the columns in whatever order suits them.
"""

from reporting.dataclasses.table_elements import (
    DateTimeTableElement,
    LinkTableElement,
    StringTableElement,
    TextTableElement,
)
from reporting.managers.montrek_table_manager import MontrekTableManager


class PipelineRegistryManagerABC(MontrekTableManager):
    status_attr: str = "status"
    message_attr: str = "message"
    status_column_name: str = "Status"
    message_column_name: str = "Message"
    date_attr: str = "created_at"
    date_column_name: str = "Created At"
    created_by_column_name: str = "Created By"

    download_url: str = ""
    download_column_name: str = "Download"
    download_hover_text: str = "Download"
    download_log_url: str = ""
    history_url: str = ""
    revoke_url: str = ""
    revoke_hover_text: str = "Revoke Task"

    # ---- column building blocks ----

    @property
    def status_element(self) -> StringTableElement:
        return StringTableElement(name=self.status_column_name, attr=self.status_attr)

    @property
    def message_element(self) -> TextTableElement:
        return TextTableElement(name=self.message_column_name, attr=self.message_attr)

    @property
    def date_element(self) -> DateTimeTableElement:
        return DateTimeTableElement(name=self.date_column_name, attr=self.date_attr)

    @property
    def created_by_element(self) -> StringTableElement:
        return StringTableElement(name=self.created_by_column_name, attr="created_by")

    @property
    def download_element(self) -> LinkTableElement:
        return LinkTableElement(
            name=self.download_column_name,
            url=self.download_url,
            kwargs={"pk": "id"},
            icon="download",
            hover_text=self.download_hover_text,
        )

    @property
    def revoke_element(self) -> LinkTableElement:
        return LinkTableElement(
            name="Stop",
            url=self.revoke_url,
            kwargs={"task_id": "celery_task_id"},
            icon="sign-stop",
            hover_text=self.revoke_hover_text,
        )

    @property
    def optional_elements(self) -> list[LinkTableElement]:
        """The log and history columns, for registries that offer them."""
        elements = []
        if self.download_log_url:
            elements.append(
                LinkTableElement(
                    name="Log",
                    url=self.download_log_url,
                    kwargs={"pk": "id"},
                    icon="download",
                    hover_text="Download Log",
                )
            )
        if self.history_url:
            elements.append(
                LinkTableElement(
                    name="History",
                    url=self.history_url,
                    kwargs={"pk": "id"},
                    icon="road",
                    hover_text="History",
                )
            )
        return elements

    # ---- assembly ----

    @property
    def table_elements(self) -> tuple:
        return (
            self.date_element,
            self.status_element,
            self.message_element,
            self.download_element,
            *self.optional_elements,
        )
