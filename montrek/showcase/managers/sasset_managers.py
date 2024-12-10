import pandas as pd
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.managers.example_data_generator import ExampleDataGeneratorABC
from showcase.models.sasset_hub_models import SAssetHub
from showcase.repositories.sasset_repositories import SAssetRepository
from showcase.repositories.scompany_repositories import SCompanyRepository


class SAssetTableManager(MontrekTableManager):
    repository_class = SAssetRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Asset", attr="asset_name"),
            te.StringTableElement(name="Asset Type", attr="asset_type"),
            te.StringTableElement(name="ISIN", attr="asset_isin"),
            te.StringTableElement(name="Company", attr="company_name"),
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
            "company_name": "Apple Inc",
        },
        {
            "asset_name": "MSFT",
            "asset_type": "EQUITY",
            "asset_isin": "US5949181045",
            "company_name": "Microsoft Corp",
        },
        {
            "asset_name": "GOOGL",
            "asset_type": "EQUITY",
            "asset_isin": "US02079K3059",
            "company_name": "Alphabet Inc",
        },
    ]

    def load(self):
        SAssetHub.objects.all().delete()
        df = pd.DataFrame(self.data)
        asset_df = df[["asset_name", "asset_type", "asset_isin"]]
        asset_repo = SAssetRepository(self.session_data)
        asset_repo.create_objects_from_data_frame(asset_df)
        hubs = asset_repo.get_hubs_by_field_values(
            values=df["asset_name"].values.tolist(),
            by_repository_field="asset_name",
        )
        df["hub_entity_id"] = [h.id for h in hubs]
        company_repo = SCompanyRepository(self.session_data)
        df["link_sasset_scompany"] = company_repo.get_hubs_by_field_values(
            values=df["company_name"].tolist(),
            by_repository_field="company_name",
        )
        link_df = df[["hub_entity_id", "link_sasset_scompany"]]
        asset_repo.create_objects_from_data_frame(link_df)
