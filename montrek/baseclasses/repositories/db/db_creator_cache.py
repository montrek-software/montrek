from typing import Protocol


class DbCreatorCacheProtocol(Protocol): ...


class DbCreatorCacheBlank(DbCreatorCacheProtocol): ...


class DbCreatorCacheFactory:
    def __init__(self, columns: list[str]):
        self.columns = columns

    def get_cache(self) -> DbCreatorCacheProtocol:
        return DbCreatorCacheBlank()
