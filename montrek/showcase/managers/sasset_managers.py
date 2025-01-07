from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.repositories.sasset_repositories import SAssetRepository


class CommonTableElementsMixin:
    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Asset", attr="asset_name"),
            te.StringTableElement(name="Asset Type", attr="asset_type"),
            te.StringTableElement(name="ISIN", attr="asset_isin"),
            te.LinkTextTableElement(
                name="Company",
                url="scompany_details",
                kwargs={"pk": "company_id"},
                hover_text="Show Company Details",
                text="company_name",
            ),
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


class SAssetTableManager(CommonTableElementsMixin, MontrekTableManager):
    repository_class = SAssetRepository


class SAssetDetailsManager(CommonTableElementsMixin, MontrekDetailsManager):
    repository_class = SAssetRepository
