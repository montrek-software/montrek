from typing import Any

from baseclasses.models import MontrekHubABC
from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses.errors.montrek_user_error import MontrekError


class ImportProcessorMixin:
    @staticmethod
    def get_hubs_for_values(
        values: list[Any],
        repository: type[MontrekRepository],
        repository_field: str,
        *,
        raise_for_multiple_hubs: bool = True,
        raise_for_unmapped_values: bool = True,
    ) -> list[MontrekHubABC | None]:
        queryset = repository().std_queryset()
        value_to_hub_map = {}
        unmapped_values = []
        multiple_hubs = []
        for obj in queryset:
            value = getattr(obj, repository_field)
            if value in value_to_hub_map:
                multiple_hubs.append(value)
            value_to_hub_map[value] = obj
        if multiple_hubs and raise_for_multiple_hubs:
            multiple_hubs_str = ", ".join(multiple_hubs[:10])
            err_msg = f"Multiple hubs found for values (truncated): {multiple_hubs_str}"
            raise MontrekError(err_msg)
        unmapped_values = [value for value in values if value not in value_to_hub_map]
        if raise_for_unmapped_values and unmapped_values:
            unmapped_values_str = ", ".join(unmapped_values[:10])
            msg = f"Cannot find hub for values (truncated): {unmapped_values_str}"
            raise MontrekError(msg)
        hubs = [value_to_hub_map.get(value) for value in values]
        return hubs
