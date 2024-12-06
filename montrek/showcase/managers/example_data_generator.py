from abc import ABC, abstractmethod


class ExampleDataGeneratorABC(ABC):
    data = []

    def __init__(self, session_data):
        self.session_data = session_data

    @abstractmethod
    def load(self):
        pass
