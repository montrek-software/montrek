import datetime
from typing import Any, TypeVar

from baseclasses.models import MontrekLinkABC, MontrekSatelliteABC, ValueDateList
from baseclasses.typing import HubValueDateProtocol, MontrekHubProtocol

type THubCacheType = dict[int, MontrekHubProtocol]
type TValueDateCacheType = dict[datetime.date | None, ValueDateList]
type THubValueDateCacheType = dict[
    tuple[int, datetime.date | None], HubValueDateProtocol
]
type TLinkCacheType = dict[tuple[type[MontrekLinkABC], int, str], MontrekLinkABC]
Data = TypeVar("Data", int, str)

type DataDict = dict[str, Any]
type SatelliteDict = dict[type[MontrekSatelliteABC], MontrekSatelliteABC]
type SatHashesMap = dict[type[MontrekSatelliteABC], str]
type SatHashesDict = dict[type[MontrekSatelliteABC], set[str]]
type HashSatMap = dict[tuple[type[MontrekSatelliteABC], str], MontrekSatelliteABC]
type HubSatMap = dict[tuple[type[MontrekSatelliteABC], int], MontrekSatelliteABC]
