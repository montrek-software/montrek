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
        return self.repository.std_create_object(**kwargs)

    def delete_object(self, pk: int):
        object_query = self.get_object_from_pk(pk)
        return self.repository.std_delete_object(object_query)

    def get_object_from_pk(self, pk: int):
        return self.repository.std_queryset().get(pk=pk)

    def get_object_from_pk_as_dict(self, pk: int) -> dict:
        object_query = self.get_object_from_pk(pk)
        return self.repository.object_to_dict(object_query)

    def get_satellite_field_choices(self) -> list[tuple]:
        field_names = sorted([f.name for f in self.repository.std_satellite_fields()])
        field_descriptions = [name.replace("_", " ").title() for name in field_names]
        return list(zip(field_names, field_descriptions))

    def collect_messages(self):
        self.messages += self.repository.messages


class MontrekManagerNotImplemented(MontrekManager):
    def __init__(self, session_data: dict[str, Any] = {}):
        raise NotImplementedError(
            "Assign valid MontrekManager class to views manager_class attribute"
        )
