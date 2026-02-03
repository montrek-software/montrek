from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from download_registry.repositories.download_registry_repositories import (
    DownloadRegistryRepository,
)


class CommonTableElementsMixin:
    @property
    def table_elements(self):
        return [
            te.LinkTableElement(
                name="Edit",
                url="download_registry_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Download Registry",
            ),
            te.LinkTableElement(
                name="Delete",
                url="download_registry_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Download Registry",
            ),
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
