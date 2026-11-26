from typing import Any

from baseclasses.dataclasses.download_type import DownloadType
from baseclasses.typing import SessionDataType
from info.managers.download_registry_storage_managers import (
    DownloadRegistryStorageManager,
)


def store_in_download_registry(
    session_data: SessionDataType,
    document_name: str,
    download_type: DownloadType,
    **kwargs: Any,
) -> None:
    DownloadRegistryStorageManager(session_data).store_in_download_registry(
        document_name, download_type
    )
