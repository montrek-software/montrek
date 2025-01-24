from abc import ABC, abstractmethod


class BaseStorageManager(ABC):
    @abstractmethod
    def save(self, file_path: str) -> str:
        pass

    @abstractmethod
    def load(self, file_name: str) -> bytes:
        pass

    @abstractmethod
    def cleanup(self):
        pass
