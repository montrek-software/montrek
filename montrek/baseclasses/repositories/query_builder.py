from typing import Any

from baseclasses.dataclasses.montrek_message import (
    MontrekMessage,
    MontrekMessageError,
)
from django.core.exceptions import FieldError
from baseclasses.repositories.annotator import Annotator
from baseclasses.repositories.filter_decoder import FilterDecoder
from django.db.models import Q, QuerySet
from django.utils import timezone


class QueryBuilder:
    def __init__(
        self,
        annotator: Annotator,
        session_data: dict[str, Any],
    ):
        self.annotator = annotator
        self.hub_class = annotator.hub_class
        self.session_data = session_data
        self.messages: list[MontrekMessage] = []

    @property
    def query_filter(self) -> Q:
        request_path = self.session_data.get("request_path", "")
        filter = self.session_data.get("filter", {})
        filter = filter.get(request_path, {})
        return FilterDecoder.decode_dict_to_query(filter)

    @property
    def hub_value_date(self):
        return self.hub_class.hub_value_date.field.model

    def build_queryset(
        self, reference_date: timezone.datetime, order_fields: tuple[str, ...] = ()
    ) -> QuerySet:
        queryset = self.hub_value_date.objects.annotate(
            **self.annotator.build(reference_date)
        ).filter(
            Q(hub__state_date_start__lte=reference_date),
            Q(hub__state_date_end__gt=reference_date),
        )
        queryset = self._apply_filter(queryset)
        queryset = self._apply_order(queryset, order_fields)
        return queryset

    def _apply_filter(self, queryset: QuerySet) -> QuerySet:
        try:
            queryset = queryset.filter(self.query_filter)
        except (FieldError, ValueError) as e:
            self.messages.append(MontrekMessageError(str(e)))
        return queryset

    def _apply_order(
        self, queryset: QuerySet, order_fields: tuple[str, ...]
    ) -> QuerySet:
        return queryset.order_by(*order_fields)
