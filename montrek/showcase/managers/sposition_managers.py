from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.repositories.sposition_repositories import SPositionRepository


class SPositionTableManager(MontrekTableManager):
    repository_class = SPositionRepository

    @property
    def table_elements(self):
        return [
            te.LinkTableElement(
                name="Edit",
                url="sposition_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Position",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sposition_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Position",
            ),
        ]
