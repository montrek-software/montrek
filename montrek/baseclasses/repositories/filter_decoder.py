from typing import Any

from django.db.models import Q


class FilterDecoder:
    @staticmethod
    def decode_dict_to_query_list(filter_dict: dict[str, Any]):
        q_objects = []
        for key, value in filter_dict.items():
            q = Q(**{key: value["filter_value"]})
            q = ~q if value["filter_negate"] else q
            q_objects.append(q)
        return q_objects
