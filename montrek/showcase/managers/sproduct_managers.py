from showcase.factories.sproduct_sat_factories import SProductSatelliteFactory
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.managers.example_data_generator import ExampleDataGeneratorABC
from showcase.repositories.sproduct_repositories import SProductRepository


class SProductTableManager(MontrekTableManager):
    repository_class = SProductRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="SProduct Name", attr="sproduct_name"),
            te.DateTableElement(name="Inception Date", attr="inception_date"),
            te.LinkTableElement(
                name="Edit",
                url="sproduct_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update SProduct",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sproduct_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete SProduct",
            ),
        ]


class SProductExampleDataGenerator(ExampleDataGeneratorABC):
    data = [
        {"sproduct_name": "Balanced Alpha", "inception_date": "2010-05-01"},
        {"sproduct_name": "Factor Plus", "inception_date": "2015-08-01"},
    ]

    def load(self):
        for record in self.data:
            SProductSatelliteFactory(
                **record, created_by_id=self.session_data["user_id"]
            )
