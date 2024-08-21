from typing import Any, TypedDict

from django.db.models import Q
from django.utils.tree import Node


class FilterType(TypedDict):
    filter_value: str | float | int | bool
    filter_negate: bool


class FilterDecoder:
    @staticmethod
    def decode_dict_to_query(
        filter_dict: dict[str, FilterType | dict[str, FilterType]],
    ) -> Q:
        q_objects = []
        for key, value in filter_dict.items():
            if key.upper() == "OR":
                q_objects.append(FilterDecoder._append_or_dict(value))
            else:
                query = FilterDecoder._set_query(key, value)
                q_objects.append(query)
        return Q(*q_objects)

    @staticmethod
    def _append_or_dict(filter_dict: dict[str, FilterType]) -> Q:
        query_or = Q()
        for key, value in filter_dict.items():
            query = FilterDecoder._set_query(key, value)
            query_or |= query
        return query_or

    @staticmethod
    def _set_query(key: str, FilterType) -> Node | Q:
        q = Q((key, FilterType["filter_value"]))
        return ~q if FilterType["filter_negate"] else q
