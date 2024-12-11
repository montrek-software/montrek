from showcase.models.stransaction_hub_models import STransactionHub
import pandas as pd
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.managers.example_data_generator import ExampleDataGeneratorABC
from showcase.repositories.sasset_repositories import SAssetRepository
from showcase.repositories.sproduct_repositories import SProductRepository
from showcase.repositories.stransaction_repositories import (
    SProductSTransactionRepository,
    STransactionRepository,
)


class STransactionTableManager(MontrekTableManager):
    repository_class = STransactionRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Product Name", attr="product_name"),
            te.StringTableElement(name="Asset Name", attr="asset_name"),
            te.DateTableElement(name="Value Date", attr="value_date"),
            te.StringTableElement(
                name="Transaction External Identifier",
                attr="transaction_external_identifier",
            ),
            te.StringTableElement(
                name="Transaction Description", attr="transaction_description"
            ),
            te.FloatTableElement(
                name="Transaction Quantity", attr="transaction_quantity"
            ),
            te.MoneyTableElement(name="Transaction Price", attr="transaction_price"),
            te.LinkTableElement(
                name="Edit",
                url="stransaction_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Transaction",
            ),
            te.LinkTableElement(
                name="Delete",
                url="stransaction_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Transaction",
            ),
        ]


class SProductSTransactionTableManager(STransactionTableManager):
    repository_class = SProductSTransactionRepository


class STransactionExampleDataGenerator(ExampleDataGeneratorABC):
    data = [
        {
            "product_name": "Balanced Alpha",
            "asset_isin": "US0378331005",
            "value_date": "2021-01-01",
            "transaction_external_identifier": "0000000001",
            "transaction_description": "security purchase",
            "transaction_quantity": 100.0,
            "transaction_price": 1.0,
        },
        {
            "product_name": "Balanced Alpha",
            "asset_isin": "US0378331005",
            "value_date": "2023-05-16",
            "transaction_external_identifier": "0000000002",
            "transaction_description": "security purchase",
            "transaction_quantity": 200.0,
            "transaction_price": 2.0,
        },
    ]

    def load(self):
        STransactionHub.objects.all().delete()
        input_df = pd.DataFrame(self.data)

        # add hub
        transaction_repo = STransactionRepository(self.session_data)
        transaction_df = input_df[
            [
                "value_date",
                "transaction_external_identifier",
                "transaction_description",
                "transaction_quantity",
                "transaction_price",
            ]
        ]
        transaction_repo.create_objects_from_data_frame(transaction_df)
        hubs = transaction_repo.get_hubs_by_field_values(
            values=input_df["transaction_external_identifier"].values.tolist(),
            by_repository_field="transaction_external_identifier",
        )
        transaction_df["hub_entity_id"] = [h.id for h in hubs]

        # add links
        product_repo = SProductRepository(self.session_data)
        transaction_df[
            "link_stransaction_sproduct"
        ] = product_repo.get_hubs_by_field_values(
            values=input_df["product_name"].values.tolist(),
            by_repository_field="product_name",
        )
        asset_repo = SAssetRepository(self.session_data)
        transaction_df[
            "link_stransaction_sasset"
        ] = asset_repo.get_hubs_by_field_values(
            values=input_df["asset_isin"].values.tolist(),
            by_repository_field="asset_isin",
        )

        transaction_repo.create_objects_from_data_frame(transaction_df)
