import pandas as pd
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.managers.example_data_generator import ExampleDataGeneratorABC
from showcase.repositories.sasset_repositories import SAssetRepository
from showcase.repositories.sproduct_repositories import SProductRepository
from showcase.repositories.stransaction_repositories import STransactionRepository


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
    ]

    def load(self):
        df = pd.DataFrame(self.data)

        # add hub
        transaction_repo = STransactionRepository(self.session_data)
        transaction_df = df[
            [
                "value_date",
                "transaction_external_identifier",
                "transaction_description",
                "transaction_quantity",
                "transaction_price",
            ]
        ]
        transaction_repo.create_objects_from_data_frame(transaction_df)

        # TODO: The hubs should already have been returned create_objects_from_data_frame
        df["hub_entity_id"] = [
            h.id
            for h in transaction_repo.get_hubs_by_field_values(
                values=df["transaction_external_identifier"].values.tolist(),
                by_repository_field="transaction_external_identifier",
            )
        ]

        # add links
        product_repo = SProductRepository(self.session_data)
        df["link_stransaction_sproduct"] = product_repo.get_hubs_by_field_values(
            values=df["product_name"].values.tolist(),
            by_repository_field="product_name",
        )
        asset_repo = SAssetRepository(self.session_data)
        df["link_stransaction_sasset"] = asset_repo.get_hubs_by_field_values(
            values=df["asset_isin"].values.tolist(),
            by_repository_field="asset_isin",
        )

        link_df = df[
            ["hub_entity_id", "link_stransaction_sproduct", "link_stransaction_sasset"]
        ]
        transaction_repo.create_objects_from_data_frame(link_df)
