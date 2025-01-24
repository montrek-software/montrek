from abc import ABC, abstractmethod


class BaseStorageManager(ABC):
    @abstractmethod
    def save(self, file_path: str):
        pass

    @abstractmethod
    def load(self) -> bytes:
        pass
