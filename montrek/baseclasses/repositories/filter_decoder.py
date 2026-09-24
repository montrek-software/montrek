from typing import TypedDict, cast

from django.db.models import Q


class FilterType(TypedDict):
    filter_value: str | float | int | bool
    filter_negate: bool


class FilterDecoder:
    @staticmethod
    def decode_dict_to_query(
        filter_dict: dict[str, FilterType | dict[str, FilterType]],
    ) -> Q:
        q_objects: list[Q] = []
        for key, value in filter_dict.items():
            if key.upper() == "OR":
                or_dict = cast(dict[str, FilterType], value)
                q_objects.append(FilterDecoder._append_or_dict(or_dict))
            else:
                query = FilterDecoder._set_query(key, cast(FilterType, value))
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
    def _set_query(key: str, filter_type: FilterType) -> Q:
        q = Q((key, filter_type["filter_value"]))
        return ~q if filter_type["filter_negate"] else q
