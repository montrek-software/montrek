from baseclasses.views import MontrekListView
from baseclasses.dataclasses.table_elements import (
    DateTableElement,
    DateTimeTableElement,
    StringTableElement,
)
from api_upload.managers.api_upload_manager import ApiUploadManager


class MontrekApiUploadView(MontrekListView):
    title = "API Uploads"

    @property
    def elements(self) -> tuple:
        return (
            StringTableElement(name="url", attr="url"),
            StringTableElement(name="Upload Status", attr="upload_status"),
            StringTableElement(name="Upload Message", attr="upload_message"),
            DateTimeTableElement(name="Upload Datetime", attr="created_at"),
        )
