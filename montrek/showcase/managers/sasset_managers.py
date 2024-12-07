from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.repositories.sasset_repositories import SAssetRepository


class SAssetTableManager(MontrekTableManager):
    repository_class = SAssetRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="SAsset Name", attr="sasset_name"),
            te.LinkTableElement(
                name="Edit",
                url="sasset_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update SAsset",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sasset_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete SAsset",
            ),
        ]
