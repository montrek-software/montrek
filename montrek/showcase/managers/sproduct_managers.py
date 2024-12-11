from reporting.managers.montrek_details_manager import MontrekDetailsManager
from showcase.factories.sproduct_sat_factories import SProductSatelliteFactory
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.managers.example_data_generator import ExampleDataGeneratorABC
from showcase.models.sproduct_hub_models import SProductHub
from showcase.repositories.sproduct_repositories import SProductRepository


class SProductTableManager(MontrekTableManager):
    repository_class = SProductRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Product Name", attr="product_name"),
            te.LinkTableElement(
                name="Details",
                url="sproduct_details",
                kwargs={"pk": "id"},
                icon="eye-open",
                hover_text="View Product Details",
            ),
            te.LinkTableElement(
                name="Edit",
                url="sproduct_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Product",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sproduct_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Product",
            ),
        ]


class SProductDetailsManager(MontrekDetailsManager):
    repository_class = SProductRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Product Name", attr="product_name"),
            te.DateTableElement(name="Inception Date", attr="inception_date"),
            te.LinkTableElement(
                name="Edit",
                url="sproduct_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Product",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sproduct_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Product",
            ),
        ]


class SProductExampleDataGenerator(ExampleDataGeneratorABC):
    data = [
        {"product_name": "Balanced Alpha", "inception_date": "2010-05-01"},
        {"product_name": "Factor Plus", "inception_date": "2015-08-01"},
    ]

    def load(self):
        SProductHub.objects.all().delete()
        for record in self.data:
            SProductSatelliteFactory(
                **record, created_by_id=self.session_data["user_id"]
            )
