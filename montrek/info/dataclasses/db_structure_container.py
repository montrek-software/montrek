from dataclasses import dataclass, field


@dataclass
class DbStructureBase:
    model_name: str
    db_table_name: str
    app: str


@dataclass
class DbStructureHub(DbStructureBase): ...


@dataclass
class DbStructureContainer:
    hubs: list[DbStructureHub] = field(default_factory=list)
