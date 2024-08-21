from typing import TypedDict

from django.db.models import Q


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
                q = Q((key, value["filter_value"]))
                q = ~q if value["filter_negate"] else q
                q_objects.append(q)
        return Q(*q_objects)

    @staticmethod
    def _append_or_dict(filter_dict: dict[str, FilterType]) -> Q:
        query = Q()
        for key, value in filter_dict.items():
            q = Q(**{key: value["filter_value"]})
            q = ~q if value["filter_negate"] else q
            query |= q
        return query
