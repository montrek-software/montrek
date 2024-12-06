from numpy import random
from baseclasses.models import ValueDateList
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.factories.transaction_hub_factories import LinkTransactionProductFactory
from showcase.factories.transaction_sat_factories import TransactionSatelliteFactory
from showcase.managers.example_data_generator import ExampleDataGeneratorABC
from showcase.repositories.product_repositories import ProductRepository
from showcase.repositories.transaction_repositories import TransactionRepository


class TransactionTableManager(MontrekTableManager):
    repository_class = TransactionRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Product Name", attr="product_name"),
            te.DateTableElement(name="Value Date", attr="value_date"),
            te.StringTableElement(
                name="Transaction Description", attr="transaction_description"
            ),
            te.StringTableElement(
                name="Transaction Quantity", attr="transaction_quantity"
            ),
            te.StringTableElement(name="Transaction Price", attr="transaction_price"),
            te.LinkTableElement(
                name="Edit",
                url="transaction_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Transaction",
            ),
            te.LinkTableElement(
                name="Delete",
                url="transaction_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Transaction",
            ),
        ]


class TransactionExampleDataGenerator(ExampleDataGeneratorABC):
    def load(self):
        products = ProductRepository().receive()
        value_dates = [vdl for vdl in ValueDateList.objects.all() if vdl.value_date]
        for i in range(50):
            product = random.choice(products)
            transaction_kwargs = {"created_by_id": self.session_data["user_id"]}
            if value_dates:
                transaction_kwargs["hub_value_date__value_date_list"] = random.choice(
                    value_dates
                )
            transaction = TransactionSatelliteFactory(**transaction_kwargs)
            LinkTransactionProductFactory(
                hub_in=transaction.hub_value_date.hub, hub_out=product.hub
            )
