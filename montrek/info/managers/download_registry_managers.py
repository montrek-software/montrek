from baseclasses.managers.montrek_manager import MontrekManager
from info.models.download_registry_sat_models import DOWNLOAD_TYPES
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from info.repositories.download_registry_repositories import (
    DownloadRegistryRepository,
)


class CommonTableElementsMixin:
    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="User", attr="created_by"),
            te.DateTimeTableElement(name="Downloaded At", attr="created_at"),
            te.StringTableElement(name="Identifier", attr="download_name"),
            te.StringTableElement(name="Type", attr="download_type"),
        ]


class DownloadRegistryTableManager(CommonTableElementsMixin, MontrekTableManager):
    repository_class = DownloadRegistryRepository

    @property
    def table_elements(self):
        table_elements = [
            te.LinkTextTableElement(
                name="Details",
                url="download_registry_details",
                kwargs={"pk": "hub_id"},
                text="hub_entity_id",
                hover_text="View Download Registry Details",
            ),
        ]
        table_elements += super().table_elements
        return table_elements


class DownloadRegistryDetailsManager(CommonTableElementsMixin, MontrekDetailsManager):
    repository_class = DownloadRegistryRepository

    @property
    def table_elements(self):
        table_elements = [
            te.StringTableElement(name="hub", attr="hub_entity_id"),
        ]
        table_elements += super().table_elements
        return table_elements


class DownloadRegistryManager(MontrekManager):
    repository_class = DownloadRegistryRepository

    def store_in_download_registry(
        self, identifier: str, download_type: DOWNLOAD_TYPES
    ):
        self.repository.create_by_dict(
            {"download_name": identifier, "download_type": download_type.value}
        )
