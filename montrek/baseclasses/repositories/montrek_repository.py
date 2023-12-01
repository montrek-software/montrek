from typing import Any, List, Dict, Type
from baseclasses.models import MontrekSatelliteABC
from django.db.models import Q, Subquery, OuterRef
from django.utils import timezone

class MontrekRepository():
    def detail_queryset(self, **kwargs):
        raise NotImplementedError('MontrekRepository has no detail_queryset method!')

    def table_queryset(self, **kwargs):
        raise NotImplementedError('MontrekRepository has no table_queryset method!')
    
    def get_satellite_field_subqueries(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        field_names: List[str],
        reference_date: timezone
    ) -> Dict[str, Subquery]:
        subqueries = {}
        for field_name in field_names:
            subquery = Subquery(
                satellite_class.objects.filter(
                    hub_entity=OuterRef('pk'),
                    state_date_start__lte=reference_date,
                    state_date_end__gt=reference_date
                ).values(field_name)
            )
            subqueries[field_name] = subquery
        return subqueries

    def get_linked_satellite_field_subqueries(
        self,
        satellite_class: Type[MontrekSatelliteABC],
        link_lookup_string: str,
        field_names: List[str],
        reference_date: timezone
    ) -> Dict[str, Subquery]:
        subqueries = {}
        for field_name in field_names:
            subquery = Subquery(
                satellite_class.objects.filter(
                    hub_entity=OuterRef(link_lookup_string),
                    #state_date_start__lte=reference_date,
                    #state_date_end__gt=reference_date
                ).values(field_name)[:1]
            )
            subqueries[field_name] = subquery
        return subqueries
