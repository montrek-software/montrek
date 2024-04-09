from baseclasses.repositories.montrek_repository import MontrekRepository


class MontrekManager:
    repository = MontrekRepository
    _repository_object = None

    @property
    def repository_object(self):
        if self._repository_object is None:
            self._repository_object = self.repository(self.session_data)
        return self._repository_object

    def show_repository_messages(self):
        for message in self.repository_object.messages:
            if message.message_type == "error":
                messages.error(self.request, message.message)
            elif message.message_type == "info":
                messages.info(self.request, message.message)
