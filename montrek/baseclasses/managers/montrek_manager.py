from baseclasses.repositories.montrek_repository import MontrekRepository
from typing import Any
from baseclasses.dataclasses.montrek_message import MontrekMessage


class MontrekManager:
    repository_class = MontrekRepository
    _repository = None

    def __init__(self, session_data: dict[str, Any] = {}):
        self.session_data = session_data
        self.messages: list[MontrekMessage] = []

    @property
    def repository(self):
        if self._repository is None:
            self._repository = self.repository_class(self.session_data)
        return self._repository

    def create_object(self, **kwargs) -> Any:
        return self.repository.create_by_dict(**kwargs)

    def delete_object(self, pk: int):
        object_query = self.get_object_from_pk(pk)
        return self.repository.delete(object_query.hub)

    def get_object_from_pk(self, pk: int):
        return self.repository.receive().get(pk=pk)

    def get_object_from_pk_as_dict(self, pk: int) -> dict:
        object_query = self.get_object_from_pk(pk)
        return self.repository.object_to_dict(object_query)

    def get_std_queryset_field_choices(self) -> list[tuple]:
        field_names = self.repository.get_all_fields()
        field_names = sorted(set(field_names))
        field_descriptions = [name.replace("_", " ").title() for name in field_names]
        return list(zip(field_names, field_descriptions))

    def collect_messages(self):
        self.messages += self.repository.messages


class MontrekManagerNotImplemented(MontrekManager):
    def __init__(self, session_data: dict[str, Any] = {}):
        raise NotImplementedError(
            "Assign valid MontrekManager class to views manager_class attribute"
        )
