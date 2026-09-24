import datetime
from typing import Any, TypeVar

from baseclasses.models import MontrekLinkABC, MontrekSatelliteBaseABC, ValueDateList
from baseclasses.typing import HubValueDateProtocol, MontrekHubProtocol

type THubCacheType = dict[int, MontrekHubProtocol]
type TValueDateCacheType = dict[datetime.date | None, ValueDateList]
type THubValueDateCacheType = dict[
    tuple[int, datetime.date | None], HubValueDateProtocol
]
type TLinkCacheType = dict[tuple[type[MontrekLinkABC], int, str], list[MontrekLinkABC]]
Data = TypeVar("Data", int, str)

type DataDict = dict[str, Any]
type SatelliteDict = dict[type[MontrekSatelliteBaseABC], MontrekSatelliteBaseABC]
type SatHashesMap = dict[type[MontrekSatelliteBaseABC], str]
type SatHashesDict = dict[type[MontrekSatelliteBaseABC], list[str]]
type HashSatMap = dict[
    tuple[type[MontrekSatelliteBaseABC], str], MontrekSatelliteBaseABC
]
type HubSatMap = dict[
    tuple[type[MontrekSatelliteBaseABC], int], MontrekSatelliteBaseABC
]
