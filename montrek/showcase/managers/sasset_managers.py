from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.factories.sasset_sat_factories import SAssetStaticSatelliteFactory
from showcase.managers.example_data_generator import ExampleDataGeneratorABC
from showcase.repositories.sasset_repositories import SAssetRepository


class SAssetTableManager(MontrekTableManager):
    repository_class = SAssetRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Asset", attr="asset_name"),
            te.StringTableElement(name="Asset Type", attr="asset_type"),
            te.StringTableElement(name="ISIN", attr="asset_isin"),
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


class SAssetExampleDataGenerator(ExampleDataGeneratorABC):
    data = [
        {
            "asset_name": "AAPL",
            "asset_type": "EQUITY",
            "asset_isin": "US0378331005",
        },
        {
            "asset_name": "MSFT",
            "asset_type": "EQUITY",
            "asset_isin": "US5949181045",
        },
        {
            "asset_name": "GOOGL",
            "asset_type": "EQUITY",
            "asset_isin": "US02079K3059",
        },
    ]

    def load(self):
        for record in self.data:
            SAssetStaticSatelliteFactory(
                **record, created_by_id=self.session_data["user_id"]
            )
