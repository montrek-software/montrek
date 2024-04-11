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

    def collect_messages(self):
        self.messages += self.repository.messages
