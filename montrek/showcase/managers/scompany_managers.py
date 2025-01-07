from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.repositories.scompany_repositories import SCompanyRepository


class CommonTableElementsMixin:
    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Company", attr="company_name"),
            te.LinkTextTableElement(
                name="Country",
                url="country_details",
                kwargs={"pk": "country_id"},
                hover_text="Show Country Details",
                text="country_name",
            ),
            te.StringTableElement(name="Sector", attr="company_sector"),
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


class SCompanyTableManager(CommonTableElementsMixin, MontrekTableManager):
    repository_class = SCompanyRepository


class SCompanyDetailsManager(CommonTableElementsMixin, MontrekDetailsManager):
    repository_class = SCompanyRepository
