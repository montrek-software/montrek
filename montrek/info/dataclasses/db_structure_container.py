from dataclasses import dataclass, field
from typing import Sequence, TypeVar


@dataclass
class DbStructureBase:
    model_name: str
    db_table_name: str
    app: str


@dataclass
class DbStructureHub(DbStructureBase): ...


@dataclass
class DbStructureHubValueDate(DbStructureBase):
    hub: str


@dataclass
class DbStructureSatellite(DbStructureBase):
    hub: str


@dataclass
class DbStructureTSSatellite(DbStructureBase):
    hub_value_date: str


@dataclass
class DbStructureLink(DbStructureBase):
    hub_in: str
    hub_out: str


T = TypeVar("T", bound=DbStructureBase)


@dataclass
class DbStructureContainer:
    hubs: list[DbStructureHub] = field(default_factory=list)
    hub_value_dates: list[DbStructureHubValueDate] = field(default_factory=list)
    sats: list[DbStructureSatellite] = field(default_factory=list)
    ts_sats: list[DbStructureTSSatellite] = field(default_factory=list)
    links: list[DbStructureLink] = field(default_factory=list)

    def find_model(self, model_name: str, models: Sequence[T]) -> T | None:
        for model in models:
            if model.model_name == model_name:
                return model
        return None

    def find_hub(self, hub_name: str) -> DbStructureHub | None:
        return self.find_model(hub_name, self.hubs)

    def find_hub_value_date(
        self, hub_value_date_name: str
    ) -> DbStructureHubValueDate | None:
        return self.find_model(hub_value_date_name, self.hub_value_dates)

    def find_sat(self, sat_name: str) -> DbStructureSatellite | None:
        return self.find_model(sat_name, self.sats)

    def find_link(self, link_name: str) -> DbStructureLink | None:
        return self.find_model(link_name, self.links)
