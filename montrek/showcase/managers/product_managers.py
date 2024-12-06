from showcase.factories.product_sat_factories import ProductSatelliteFactory
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.managers.example_data_generator import ExampleDataGeneratorABC
from showcase.repositories.product_repositories import ProductRepository


class ProductTableManager(MontrekTableManager):
    repository_class = ProductRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Product Name", attr="product_name"),
            te.DateTableElement(name="Inception Date", attr="inception_date"),
            te.LinkTableElement(
                name="Edit",
                url="product_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Product",
            ),
            te.LinkTableElement(
                name="Delete",
                url="product_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Product",
            ),
        ]


class ProductExampleDataGenerator(ExampleDataGeneratorABC):
    data = [
        {"product_name": "Balanced Alpha", "inception_date": "2010-05-01"},
        {"product_name": "Factor Plus", "inception_date": "2015-08-01"},
    ]

    def load(self):
        for record in self.data:
            ProductSatelliteFactory(
                **record, created_by_id=self.session_data["user_id"]
            )
