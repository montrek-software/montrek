"""Shared table columns for registries of pipeline runs.

Uploads and exports show the same thing — what ran, how it went, and what came
out of it — so the column building blocks live here. Subclasses name the status
and message fields and assemble the columns in whatever order suits them.

Shown by a list view, the status label of a run that is still active refreshes
its row, message included, as the background worker moves the run on (see
``LiveLabelTableElement``); set ``live_status = False`` to keep it still.
"""

from process_pipeline.constants import RegistryStatusTextChoices
from process_pipeline.dataclasses.registry_table_elements import (
    LIVE_SHOWN_MESSAGE_PARAM,
    RegistryMessageTableElement,
    RegistryStatusTableElement,
)
from reporting.dataclasses.table_elements import (
    LIVE_SHOWN_PARAM,
    DateTimeTableElement,
    LabelTableElement,
    LinkTableElement,
    StringTableElement,
    TextTableElement,
)
from reporting.managers.montrek_table_manager import MontrekTableManager


class PipelineRegistryManagerABC(MontrekTableManager):
    registry_status_text_choices: type[RegistryStatusTextChoices]

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
    live_status: bool = True
    status_poll_interval: int = 3

    # ---- column building blocks ----

    @property
    def status_element(self) -> LabelTableElement:
        if not self.live_status:
            return LabelTableElement(
                name=self.status_column_name,
                attr=self.status_attr,
                color_codes=self.registry_status_text_choices.label_colors(),
            )
        return RegistryStatusTableElement(
            name=self.status_column_name,
            attr=self.status_attr,
            color_codes=self.registry_status_text_choices.label_colors(),
            rows_path=self.live_rows_path,
            active_values=self.registry_status_text_choices.active_labels(),
            poll_interval=self.status_poll_interval,
            previous_value=self._get_shown_param(LIVE_SHOWN_PARAM),
            message_attr=self.message_attr,
        )

    @property
    def message_element(self) -> TextTableElement:
        return RegistryMessageTableElement(
            name=self.message_column_name,
            attr=self.message_attr,
            previous_digest=self._get_shown_param(LIVE_SHOWN_MESSAGE_PARAM),
        )

    def _get_shown_param(self, key: str) -> str | None:
        """What a polling status label last showed; None outside a poll."""
        value = self.session_data.get(key)
        if isinstance(value, list | tuple):
            value = value[0] if value else None
        return None if value is None else str(value)

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
