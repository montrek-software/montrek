from typing import Any

from django.db.models import Q


class FilterDecoder:
    @staticmethod
    def decode_dict_to_query_list(
        filter_dict: dict[str, dict[str, str | bool]],
    ) -> list[Q]:
        q_objects = []
        for key, value in filter_dict.items():
            if key.upper() == "OR":
                q_objects.append(FilterDecoder._append_or_dict(value))
            else:
                q = Q(**{key: value["filter_value"]})
                q = ~q if value["filter_negate"] else q
                q_objects.append(q)
        return q_objects

    @staticmethod
    def _append_or_dict(filter_dict) -> Q:
        query = Q()
        for key, value in filter_dict.items():
            q = Q(**{key: value["filter_value"]})
            q = ~q if value["filter_negate"] else q
            query |= q
        return query
