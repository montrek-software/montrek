from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from user.repositories.montrek_user_repositories import MontrekUserRepository


class CommonTableElementsMixin:
    @property
    def table_elements(self):
        return [
            te.LinkTableElement(
                name="Edit",
                url="montrek_user_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update MontrekUser",
            ),
            te.LinkTableElement(
                name="Delete",
                url="montrek_user_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete MontrekUser",
            ),
        ]


class MontrekUserTableManager(CommonTableElementsMixin, MontrekTableManager):
    repository_class = MontrekUserRepository

    @property
    def table_elements(self):
        table_elements = [
            te.LinkTableElement(
                name="Details",
                url="montrek_user_details",
                kwargs={"pk": "hub_id"},
                icon="eye-open",
                hover_text="View MontrekUser Details",
            ),
        ]
        table_elements += super().table_elements
        return table_elements


class MontrekUserDetailsManager(CommonTableElementsMixin, MontrekDetailsManager):
    repository_class = MontrekUserRepository
