from typing import Any, cast

from baseclasses.typing import SessionDataType
from django.contrib import messages
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest
from process_pipeline.functions.selection import get_dotted_path

from file_upload.forms import SimpleUploadFileForm
from file_upload.managers.simple_upload_file_manager import (
    TABLE_MANAGER_KEY,
    SimpleUploadFileManager,
)


class SimpleFileUpload:
    """The file upload of a ``MontrekListView`` with ``do_simple_file_upload``,
    registered in ``FileUploadConfig``: loads the rows of a dropped file into
    the repository of the list's table manager."""

    accepted_file_types = ".xlsx,.csv"

    def get_form(self, *args: Any) -> SimpleUploadFileForm:
        return SimpleUploadFileForm(self.accepted_file_types, *args)

    def upload(
        self,
        request: HttpRequest,
        session_data: SessionDataType,
        table_manager_class: type,
        view_kwargs: dict[str, Any],
    ) -> None:
        form = self.get_form(request.POST, request.FILES)
        if not form.is_valid():
            return
        session_data = session_data.copy()
        session_data["overwrite"] = form.cleaned_data["overwrite"]
        file_upload_manager = SimpleUploadFileManager(
            session_data=session_data, **view_kwargs
        )
        file_upload_manager.set_pipeline_data(
            {TABLE_MANAGER_KEY: get_dotted_path(table_manager_class)}
        )
        uploaded_file = cast(UploadedFile, request.FILES["file"])
        result = file_upload_manager.upload_and_process(uploaded_file)
        processor = file_upload_manager.processor
        message = processor.message if processor is not None else ""
        if result:
            messages.info(request, message)
        else:
            messages.error(request, message)
