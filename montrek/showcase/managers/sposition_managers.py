from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.repositories.stransaction_repositories import (
    SProductSPositionRepository,
)


class SPositionTableManager(MontrekTableManager):
    repository_class = SProductSPositionRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(
                name="Product Name",
                attr="product_name",
            ),
            te.LinkTextTableElement(
                name="Asset Name",
                url="sasset_details",
                kwargs={"pk": "asset_id"},
                hover_text="Show Asset Details",
                text="asset_name",
            ),
            te.FloatTableElement(
                name="Position Quantity",
                attr="position_quantity",
            ),
            te.FloatTableElement(
                name="Price",
                attr="price",
            ),
        ]
