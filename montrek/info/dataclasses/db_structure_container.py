from dataclasses import dataclass, field


@dataclass
class DbStructureBase:
    model_name: str
    db_table_name: str
    app: str


@dataclass
class DbStructureHub(DbStructureBase): ...


@dataclass
class DbStructureHubValueDate(DbStructureBase): ...


@dataclass
class DbStructureSatellite(DbStructureBase): ...


@dataclass
class DbStructureTSSatellite(DbStructureBase): ...


@dataclass
class DbStructureLink(DbStructureBase): ...


@dataclass
class DbStructureContainer:
    hubs: list[DbStructureHub] = field(default_factory=list)
    hub_value_dates: list[DbStructureHubValueDate] = field(default_factory=list)
    sats: list[DbStructureSatellite] = field(default_factory=list)
    ts_sats: list[DbStructureTSSatellite] = field(default_factory=list)
    links: list[DbStructureLink] = field(default_factory=list)
