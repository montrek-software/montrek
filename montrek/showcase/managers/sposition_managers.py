from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.repositories.stransaction_repositories import SPositionRepository


class SPositionTableManager(MontrekTableManager):
    repository_class = SPositionRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(
                name="Product Name",
                attr="product_name",
            ),
            te.StringTableElement(
                name="Asset Name",
                attr="asset_name",
            ),
            te.FloatTableElement(
                name="Position Quantity",
                attr="position_quantity",
            ),
        ]
