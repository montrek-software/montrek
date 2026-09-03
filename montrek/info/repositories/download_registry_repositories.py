from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses.typing import SessionDataType
from info.models.download_registry_hub_models import DownloadRegistryHub
from info.models.download_registry_sat_models import (
    DownloadRegistrySatellite,
)


class DownloadRegistryRepository(MontrekRepository):
    """Record of who downloaded what, when.

    Any ``reference_date`` in the incoming session data is dropped.  Every
    caller hands its whole view session data to
    ``DownloadRegistryStorageManager``, and a download view may legitimately be
    reading a past state -- a report rendered as of a frozen risk procedure, or
    a redemption plan for an earlier ``reference_date`` passed as a query
    parameter.  This entry is not part of that state: it records the act of
    downloading, which happens now, and the write guard in ``create_by_dict``
    would otherwise refuse it.
    """

    hub_class = DownloadRegistryHub
    default_order_fields = ("-created_at",)

    def __init__(self, session_data: SessionDataType | None = None):
        session_data = dict(session_data or {})
        session_data.pop("reference_date", None)
        super().__init__(session_data)

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            DownloadRegistrySatellite, ["download_name", "download_type"]
        )
