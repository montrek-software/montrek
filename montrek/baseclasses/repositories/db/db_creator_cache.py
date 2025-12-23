import datetime
import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, cast

from baseclasses.models import MontrekLinkABC, MontrekSatelliteABC, ValueDateList
from baseclasses.repositories.db.db_staller import DbStallerProtocol
from baseclasses.repositories.db.satellite_creator import SatelliteCreator
from baseclasses.repositories.db.typing import (
    DataDict,
    HashSatMap,
    HubSatMap,
    SatHashesDict,
    THubCacheType,
    THubValueDateCacheType,
    TLinkCacheType,
    TValueDateCacheType,
)
from baseclasses.typing import HubValueDateProtocol, MontrekHubProtocol
from baseclasses.utils import datetime_to_montrek_time, to_date
from django.db.models import ManyToManyField, Q
from django.utils import timezone

logger = logging.getLogger(__name__)

HUB_ENTITY_COLUMN = "hub_entity_id"
VALUE_DATE_COLUMN = "value_date"


class LinkDirection(str, Enum):
    HUB_IN = "hub_in"
    HUB_OUT = "hub_out"


@dataclass(frozen=True, slots=True)
class SatelliteKey:
    sat_class: type[MontrekSatelliteABC]
    hash_identifier: str


@dataclass(frozen=True, slots=True)
class SatelliteHubKey:
    sat_class: type[MontrekSatelliteABC]
    hub_id: int


@dataclass(frozen=True, slots=True)
class HubValueDateKey:
    hub_id: int
    value_date: datetime.date | None


@dataclass(frozen=True, slots=True)
class LinkKey:
    link_class: type[MontrekLinkABC]
    hub_id: int
    direction: LinkDirection


class DbCreatorCache:
    """
    Cache object with explicit phases and stable invariants.

    Key invariants:
    - All cache dicts are always initialized in __init__.
    - Public entrypoint is cache_with_data(); other methods are implementation details.
    - Cache methods populate only their own cache; dependency expansion happens via explicit return values.
    """

    satellite_creator_class: type[SatelliteCreator] = SatelliteCreator

    def __init__(self, db_staller: DbStallerProtocol, *, now=None):
        self.db_staller = db_staller
        self.satellite_creator = self.satellite_creator_class()

        # Time anchor for validity filtering
        self.now = now or timezone.now()

        # Input/derived ID sets (kept separate)
        self.initial_hub_ids: set[int] = set()
        self.derived_hub_ids: set[int] = set()

        # Caches (always initialized)
        self.cached_hubs: THubCacheType = {}
        self.cached_value_date_lists: TValueDateCacheType = {}
        self.cached_hub_value_dates: THubValueDateCacheType = {}
        self.cached_satellites: HashSatMap = {}
        self.cached_satellites_by_hub: HubSatMap = {}
        self.cached_links: TLinkCacheType = {}

    # -------------------------
    # Public orchestration
    # -------------------------

    def cache_with_data(self, data: list[DataDict]) -> None:
        if not data:
            return

        self.initial_hub_ids = self._extract_hub_ids(data)
        value_dates = self._extract_value_dates(data)
        columns = set(data[0].keys())

        # Phase 1: direct caches from raw inputs
        self._cache_hubs(self.initial_hub_ids)
        self._cache_value_dates(value_dates)
        self._cache_hub_value_dates(self.initial_hub_ids, value_dates)

        # Phase 2: satellites from hashes + dependency expansion
        sat_hashes = self._compute_sat_hashes(data)
        sats_by_hash, derived_hubs, derived_hvds = self._cache_satellites_by_hashes(
            sat_hashes
        )

        # Expand dependency caches explicitly
        self.derived_hub_ids = derived_hubs
        all_hub_ids = set(self.initial_hub_ids) | set(self.derived_hub_ids)

        # Ensure hubs/hvds needed by satellites exist in caches
        self._cache_hubs(all_hub_ids)
        self._merge_hub_value_dates(derived_hvds)

        # Phase 3: satellites from hubs (excluding already-known hashes)
        sats_from_hubs = self._cache_satellites_from_hubs(
            all_hub_ids=all_hub_ids, sat_hashes=sat_hashes
        )

        # Finalize satellites cache
        self.cached_satellites = {}
        self.cached_satellites.update(sats_by_hash)
        self.cached_satellites.update(sats_from_hubs)

        # Phase 4: links
        self._cache_links(columns=columns, hub_ids=all_hub_ids)

    # -------------------------
    # Extractors
    # -------------------------

    def _extract_hub_ids(self, data: Iterable[DataDict]) -> set[int]:
        hub_ids: set[int] = set()
        for dt in data:
            value = dt.get(HUB_ENTITY_COLUMN)
            if value is None:
                continue
            hub_ids.add(int(value))
        return hub_ids

    def _extract_value_dates(
        self, data: Iterable[DataDict]
    ) -> set[datetime.date | None]:
        # Keep None out of this set unless explicitly present in input via to_date
        value_dates: set[datetime.date | None] = set()
        for dt in data:
            value = dt.get(VALUE_DATE_COLUMN)
            if not value:
                continue
            value_dates.add(to_date(value))
        return value_dates

    # -------------------------
    # Caching primitives (populate only their own cache)
    # -------------------------

    def _cache_hubs(self, hub_ids: set[int]) -> None:
        missing = hub_ids - set(self.cached_hubs.keys())
        if not missing:
            return

        logger.debug("Caching %d hubs", len(missing))
        hub_class = self.db_staller.hub_class
        hubs = hub_class.objects.filter(id__in=missing)
        for hub in hubs:
            self.cached_hubs[hub.id] = hub
        logger.debug("End cache hubs")

    def _cache_value_dates(self, value_dates: set[datetime.date | None]) -> None:
        logger.debug("Start cache value_dates")

        # If you want True None-support, you may include None explicitly, but existing
        # code always queried NULL anyway. We keep that behavior.
        value_dates_lists = ValueDateList.objects.filter(
            Q(value_date__in=value_dates) | Q(value_date__isnull=True)
        )
        for vdl in value_dates_lists:
            self.cached_value_date_lists[vdl.value_date] = vdl

        logger.debug("End cache value_dates")

    def _cache_hub_value_dates(
        self, hub_ids: set[int], value_dates: set[datetime.date | None]
    ) -> None:
        logger.debug("Start cache hub_value_dates")

        # Query all candidate HVDs for these hubs and dates
        hub_value_dates = self.db_staller.hub_value_date_class.objects.select_related(
            "value_date_list", "hub"
        ).filter(
            Q(hub__id__in=hub_ids)
            & (
                Q(value_date_list__value_date__in=value_dates)
                | Q(value_date_list__value_date__isnull=True)
            )
        )

        for hvd in hub_value_dates:
            key = HubValueDateKey(hvd.hub_id, hvd.value_date_list.value_date)
            self.cached_hub_value_dates[(key.hub_id, key.value_date)] = hvd

        logger.debug("End cache hub_value_dates")

    def _merge_hub_value_dates(
        self, hvds: dict[HubValueDateKey, HubValueDateProtocol]
    ) -> None:
        # Merge without overwriting existing entries
        for key, hvd in hvds.items():
            self.cached_hub_value_dates.setdefault((key.hub_id, key.value_date), hvd)

    # -------------------------
    # Satellite caching
    # -------------------------

    def _compute_sat_hashes(self, data: Iterable[DataDict]) -> SatHashesDict:
        sat_hashes: SatHashesDict = {}

        # Static satellites: hash from identifier fields in each row
        for sat_class in self.db_staller.get_static_satellite_classes():
            hashes: list[str] = []
            for data_item in data:
                identifier_parts: list[str] = []
                for id_field in sat_class.identifier_fields:
                    value = data_item.get(id_field, "")
                    if isinstance(value, datetime.datetime):
                        value = datetime_to_montrek_time(value)
                    identifier_parts.append(str(value))
                identifier_string = "".join(identifier_parts)
                hashes.append(sat_class.convert_string_to_hash(identifier_string))
            sat_hashes[sat_class] = hashes

        # Timeseries satellites: hash from hub_value_date.id
        for sat_class in self.db_staller.get_ts_satellite_classes():
            hashes: list[str] = []
            for hvd in self.cached_hub_value_dates.values():
                hashes.append(sat_class.convert_string_to_hash(str(hvd.id)))
            sat_hashes[sat_class] = hashes

        return sat_hashes

    def _cache_satellites_by_hashes(
        self, sat_hashes: SatHashesDict
    ) -> tuple[HashSatMap, set[int], dict[HubValueDateKey, HubValueDateProtocol]]:
        """
        First pass: fetch satellites by hash_identifier.
        Returns:
          - satellites cache map (by SatelliteKey)
          - derived hub ids referenced by these satellites
          - derived hub_value_dates referenced by these satellites
        """
        cache: dict[SatelliteKey, MontrekSatelliteABC] = {}
        derived_hub_ids: set[int] = set()
        derived_hvds: dict[HubValueDateKey, HubValueDateProtocol] = {}

        for sat_class, hashes in sat_hashes.items():
            if not hashes:
                continue
            qs = self._filter_satellites(
                sat_class=sat_class,
                extra_filter=Q(hash_identifier__in=hashes),
            )
            for sat in qs:
                cache[SatelliteKey(sat_class, sat.hash_identifier)] = sat

                if sat_class.is_timeseries:
                    hvd = sat.hub_value_date
                    hub = hvd.hub
                    derived_hub_ids.add(hub.id)
                    derived_hvds[
                        HubValueDateKey(hvd.hub_id, hvd.value_date_list.value_date)
                    ] = hvd
                else:
                    hub = sat.hub_entity
                    derived_hub_ids.add(hub.id)
                    # Non-timeseries: key it under (hub_id, None) to preserve prior behavior
                    hvd = hub.hub_value_date
                    derived_hvds[HubValueDateKey(hub.id, None)] = hvd

        # Convert to the original HashSatMap shape: (class, hash) tuple keys
        return (
            cast(
                HashSatMap,
                {(k.sat_class, k.hash_identifier): v for k, v in cache.items()},
            ),
            derived_hub_ids,
            derived_hvds,
        )

    def _cache_satellites_from_hubs(
        self, *, all_hub_ids: set[int], sat_hashes: SatHashesDict
    ) -> HashSatMap:
        """
        Second pass: fetch additional satellites for those hubs, excluding the hashes already computed.
        Populates only satellites; does not mutate hub/hvd caches.
        """
        cache: dict[SatelliteKey, MontrekSatelliteABC] = {}

        for sat_class, hashes in sat_hashes.items():
            sat_is_timeseries = sat_class.is_timeseries
            hub_filter = (
                "hub_value_date__hub_id" if sat_is_timeseries else "hub_entity_id"
            )
            extra_filter = Q(**{f"{hub_filter}__in": all_hub_ids}) & ~Q(
                hash_identifier__in=hashes or []
            )
            qs = self._filter_satellites(sat_class=sat_class, extra_filter=extra_filter)

            for sat in qs:
                cache[SatelliteKey(sat_class, sat.hash_identifier)] = sat
                if not sat_is_timeseries:
                    self.cached_satellites_by_hub[(sat_class, sat.hub_entity_id)] = sat

        return cast(
            HashSatMap, {(k.sat_class, k.hash_identifier): v for k, v in cache.items()}
        )

    def _filter_satellites(
        self, *, sat_class: type[MontrekSatelliteABC], extra_filter: Q
    ):
        """
        Centralized validity filtering.
        """
        if sat_class.is_timeseries:
            relate_fields = (
                "hub_value_date",
                "hub_value_date__value_date_list",
                "hub_value_date__hub",
            )
            # Ensure BOTH the satellite and its hub are currently valid
            validity_filter = (
                Q(state_date_start__lte=self.now)
                & Q(state_date_end__gt=self.now)
                & Q(hub_value_date__hub__state_date_end__gt=self.now)
            )
        else:
            relate_fields = ("hub_entity",)
            validity_filter = (
                Q(state_date_start__lte=self.now)
                & Q(state_date_end__gt=self.now)
                & Q(hub_entity__state_date_end__gt=self.now)
            )

        return sat_class.objects.select_related(*relate_fields).filter(
            validity_filter, extra_filter
        )

    # -------------------------
    # Link caching
    # -------------------------

    def _cache_links(self, *, columns: set[str], hub_ids: set[int]) -> None:
        """
        Cache existing links for the given hub IDs and link field names.
        Stores links in a dict keyed by (link_class, hub_id, direction).
        """
        logger.debug("Start cache links")

        cached_links: dict[LinkKey, list[MontrekLinkABC]] = defaultdict(list)

        link_classes = self._get_link_classes_for_fields(columns)
        if not link_classes or not hub_ids:
            self.cached_links = {}
            logger.debug("End cache links")
            return

        for link_class in link_classes:
            links = link_class.objects.select_related("hub_in", "hub_out").filter(
                Q(hub_in_id__in=hub_ids) | Q(hub_out_id__in=hub_ids),
                state_date_start__lte=self.now,
                state_date_end__gt=self.now,
            )

            for link in links:
                if link.hub_in_id in hub_ids:
                    cached_links[
                        LinkKey(link_class, link.hub_in_id, LinkDirection.HUB_IN)
                    ].append(link)
                if link.hub_out_id in hub_ids:
                    cached_links[
                        LinkKey(link_class, link.hub_out_id, LinkDirection.HUB_OUT)
                    ].append(link)

        # Convert to the original TLinkCacheType key shape if needed:
        # (link_class, hub_id, "hub_in"/"hub_out") -> list[link]
        self.cached_links = {
            (k.link_class, k.hub_id, k.direction.value): v
            for k, v in cached_links.items()
        }

        logger.debug("End cache links")

    def _get_link_classes_for_fields(
        self, field_names: set[str]
    ) -> list[type[MontrekLinkABC]]:
        """
        Extract link classes that correspond to specific field names in the data.

        This keeps your introspection approach, but makes the "is link model" check robust
        by using issubclass() instead of MRO name matching.
        """
        from django.db.models.fields.related import ManyToOneRel

        link_classes: list[type[MontrekLinkABC]] = []

        for field in self.db_staller.hub_class._meta.get_fields():
            if field.name not in field_names:
                continue

            through_model = None

            if getattr(field, "many_to_many", False) and hasattr(field, "through"):
                through_model = field.through
            elif isinstance(field, ManyToOneRel):
                through_model = field.related_model
            elif isinstance(field, ManyToManyField):
                through_model = field.remote_field.through

            if (
                through_model
                and isinstance(through_model, type)
                and issubclass(through_model, MontrekLinkABC)
            ):
                link_classes.append(cast(type[MontrekLinkABC], through_model))

        return link_classes

    # -------------------------
    # Public accessors
    # -------------------------

    def get_cached_satellite(
        self, satellite_class: type[MontrekSatelliteABC], hash_identifier: str
    ) -> MontrekSatelliteABC | None:
        return self.cached_satellites.get((satellite_class, hash_identifier))

    def get_cached_satellite_by_hub(
        self, satellite_class: type[MontrekSatelliteABC], hub_id: int
    ) -> MontrekSatelliteABC | None:
        return self.cached_satellites_by_hub.get((satellite_class, hub_id))

    def get_cached_hub(self, hub_entity_id: int) -> MontrekHubProtocol | None:
        return self.cached_hubs.get(hub_entity_id)

    def get_cached_value_date(
        self, value_date: datetime.date | None
    ) -> ValueDateList | None:
        return self.cached_value_date_lists.get(value_date)

    def get_cached_hub_value_date(
        self, hub_entity_id: int, value_date: datetime.date | None
    ) -> HubValueDateProtocol | None:
        return self.cached_hub_value_dates.get((hub_entity_id, value_date))

    def get_cached_links(
        self,
        link_class: type[MontrekLinkABC],
        hub_entity_id: int,
        direction: LinkDirection | str,
    ) -> list[MontrekLinkABC]:
        """
        Returns a list (possibly empty), not None. This matches how the cache is built.
        """
        dir_value = (
            direction.value if isinstance(direction, LinkDirection) else str(direction)
        )
        return self.cached_links.get((link_class, hub_entity_id, dir_value), [])
