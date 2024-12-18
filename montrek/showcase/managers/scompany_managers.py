from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
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
