from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.factories.scompany_sat_factories import SCompanyStaticSatelliteFactory
from showcase.managers.example_data_generator import ExampleDataGeneratorABC
from showcase.repositories.scompany_repositories import SCompanyRepository


class SCompanyTableManager(MontrekTableManager):
    repository_class = SCompanyRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Company", attr="company_name"),
            te.LinkTableElement(
                name="Edit",
                url="scompany_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update SCompany",
            ),
            te.LinkTableElement(
                name="Delete",
                url="scompany_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete SCompany",
            ),
        ]


class SCompanyExampleDataGenerator(ExampleDataGeneratorABC):
    data = [
        {"company_name": "Apple Inc"},
        {"company_name": "Microsoft Corp"},
        {"company_name": "Alphabet Inc"},
    ]

    def load(self):
        for record in self.data:
            SCompanyStaticSatelliteFactory(
                **record, created_by_id=self.session_data["user_id"]
            )
