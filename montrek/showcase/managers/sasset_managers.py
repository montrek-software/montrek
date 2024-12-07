from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.repositories.sasset_repositories import SAssetRepository


class SAssetTableManager(MontrekTableManager):
    repository_class = SAssetRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Asset Name", attr="asset_name"),
            te.StringTableElement(name="Asset Type", attr="asset_type"),
            te.LinkTableElement(
                name="Edit",
                url="sasset_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Asset",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sasset_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Asset",
            ),
        ]
