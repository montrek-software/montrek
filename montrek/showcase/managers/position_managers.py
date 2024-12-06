from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.repositories.position_repositories import PositionRepository


class PositionTableManager(MontrekTableManager):
    repository_class = PositionRepository

    @property
    def table_elements(self):
        return [
            te.LinkTableElement(
                name="Edit",
                url="position_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Position",
            ),
            te.LinkTableElement(
                name="Delete",
                url="position_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Position",
            ),
        ]
