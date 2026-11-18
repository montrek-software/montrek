import datetime
from collections.abc import Callable, Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from django.db.models.constants import LOOKUP_SEP

TRUE_VALUES = ("True", "true", True)
FALSE_VALUES = ("False", "false", False)


class DataFrameFilterError(ValueError):
    pass


class DataFrameFilter:
    """The filter of a list view, as stored in the session, applied to the rows
    of a DataFrame table.

    Mirrors the filter the query builder applies to a queryset: the keys are
    ``<column>__<lookup>``, all of them must hold, and the entries under an
    ``OR`` key form a group of which one must hold. The value is converted to
    the type of the column, as the database casts it to the type of the field.
    As in SQL, a comparison with an empty value is not true, negated or not.
    """

    LOOKUPS: Mapping[str, Callable[[pd.Series, Any], pd.Series]] = {
        "exact": lambda column, value: column == value,
        "iexact": lambda column, value: column.astype(str).str.casefold()
        == str(value).casefold(),
        "contains": lambda column, value: column.astype(str).str.contains(
            str(value), regex=False
        ),
        "startswith": lambda column, value: column.astype(str).str.startswith(
            str(value)
        ),
        "endswith": lambda column, value: column.astype(str).str.endswith(str(value)),
        "gt": lambda column, value: column > value,
        "gte": lambda column, value: column >= value,
        "lt": lambda column, value: column < value,
        "lte": lambda column, value: column <= value,
        "in": lambda column, value: column.isin(value),
    }

    def __init__(self, filter_dict: Mapping[str, Any]):
        self.filter_dict = filter_dict

    def mask(self, df: pd.DataFrame) -> pd.Series:
        """True for the rows that pass the filter.

        Raises ``DataFrameFilterError`` (or the ``TypeError`` of an impossible
        comparison) if the filter cannot be applied."""
        mask = pd.Series(True, index=df.index)
        for key, filter_type in self.filter_dict.items():
            if key.upper() == "OR":
                if filter_type:
                    mask &= self._any_mask(df, filter_type)
            else:
                mask &= self._condition(df, key, filter_type)
        return mask

    def _any_mask(self, df: pd.DataFrame, filter_dict: Mapping[str, Any]) -> pd.Series:
        mask = pd.Series(False, index=df.index)
        for key, filter_type in filter_dict.items():
            mask |= self._condition(df, key, filter_type)
        return mask

    def _condition(
        self, df: pd.DataFrame, key: str, filter_type: Mapping[str, Any]
    ) -> pd.Series:
        field, lookup = self._split_key(key)
        if field not in df.columns:
            raise DataFrameFilterError(f"Cannot resolve keyword '{field}'")
        column = df[field]
        value = filter_type["filter_value"]
        if lookup == "isnull":
            condition = column.isna() if self._to_bool(value) else column.notna()
            return ~condition if filter_type["filter_negate"] else condition
        present = column.notna()
        values = column[present]
        if values.empty:
            return pd.Series(False, index=df.index)
        converted = self._convert(values, value, is_list=lookup == "in")
        condition = (
            self.LOOKUPS[lookup](values, converted)
            .astype(bool)
            .reindex(df.index, fill_value=False)
        )
        if filter_type["filter_negate"]:
            return ~condition & present
        return condition

    def _split_key(self, key: str) -> tuple[str, str]:
        field, _, lookup = key.rpartition(LOOKUP_SEP)
        if field and (lookup in self.LOOKUPS or lookup == "isnull"):
            return field, lookup
        return key, "exact"

    def _convert(self, values: pd.Series, value: Any, is_list: bool) -> Any:
        convert = self._converter(values)
        try:
            if is_list:
                items = value if isinstance(value, list | tuple) else [value]
                return [convert(item) for item in items]
            return convert(value)
        except (TypeError, ValueError, InvalidOperation) as e:
            raise DataFrameFilterError(
                f"'{value}' does not fit the column '{values.name}'"
            ) from e

    @classmethod
    def _converter(cls, values: pd.Series) -> Callable[[Any], Any]:
        """Converts a filter value to the type of the values of the column."""
        if pd.api.types.is_bool_dtype(values):
            return cls._to_bool
        if pd.api.types.is_integer_dtype(values):
            return cls._to_int
        if pd.api.types.is_float_dtype(values):
            return float
        if pd.api.types.is_datetime64_any_dtype(values):
            return cls._to_timestamp
        return cls._object_converter(values.iloc[0])

    @classmethod
    def _object_converter(cls, sample: Any) -> Callable[[Any], Any]:
        # datetime first, as a datetime is a date as well
        converters: tuple[tuple[type, Callable[[Any], Any]], ...] = (
            (bool, cls._to_bool),
            (int, cls._to_int),
            (float, float),
            (Decimal, lambda value: Decimal(str(value))),
            (datetime.datetime, cls._to_timestamp),
            (datetime.date, cls._to_date),
        )
        for sample_type, converter in converters:
            if isinstance(sample, sample_type):
                return converter
        return str

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if value in TRUE_VALUES:
            return True
        if value in FALSE_VALUES:
            return False
        raise ValueError(f"'{value}' is not a boolean")

    @staticmethod
    def _to_int(value: Any) -> int:
        # As the database does, "1.0" is no integer
        return value if isinstance(value, int) else int(str(value))

    @staticmethod
    def _to_timestamp(value: Any) -> pd.Timestamp:
        return pd.Timestamp(value)

    @staticmethod
    def _to_date(value: Any) -> datetime.date:
        if isinstance(value, datetime.date):
            return value
        return datetime.date.fromisoformat(str(value))
