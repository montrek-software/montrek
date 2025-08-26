from dataclasses import dataclass


@dataclass
class DbStructureBase:
    model_name: str
    app: str


@dataclass
class DbStructureHub(DbStructureBase): ...


@dataclass
class DbStructureContainer:
    hubs: list[DbStructureHub]
