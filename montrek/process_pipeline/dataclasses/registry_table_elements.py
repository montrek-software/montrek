import zlib
from dataclasses import dataclass
from typing import Any

from reporting.dataclasses.table_elements import (
    LiveLabelTableElement,
    TdClassesType,
    TextTableElement,
)

# Query parameter carrying the digest of the message a live row last showed.
LIVE_SHOWN_MESSAGE_PARAM = "live_shown_message"


@dataclass
class RegistryMessageTableElement(TextTableElement):
    """The message of a pipeline run, marked when it changed since last shown.

    ``previous_digest`` is the digest the polling status label sent along with
    the row it last showed; the message itself would bloat the poll URL.
    """

    previous_digest: str | None = None

    @staticmethod
    def digest(message: Any) -> str:
        text = "" if message is None else str(message)
        return format(zlib.crc32(text.encode()), "x")

    def get_td_classes(self, value: Any, obj: Any) -> TdClassesType:
        td_classes = [*super().get_td_classes(value, obj)]
        if self.previous_digest not in (None, self.digest(value)):
            td_classes.append("mt-live-cell-changed")
        return td_classes


@dataclass
class RegistryStatusTableElement(LiveLabelTableElement):
    """The status of a pipeline run, refreshing its row while the run is active.

    Sends the digest of the row's message along with the poll, so the message
    column can mark a change as well.
    """

    message_attr: str = "message"

    def get_poll_params(self, value: Any, obj: Any) -> dict[str, str]:
        params = super().get_poll_params(value, obj)
        message = self.get_dotted_attr_or_arg(obj, self.message_attr)
        params[LIVE_SHOWN_MESSAGE_PARAM] = RegistryMessageTableElement.digest(message)
        return params
