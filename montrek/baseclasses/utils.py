from abc import ABC, abstractmethod
import datetime
from datetime import timedelta
from typing import Tuple

from django.utils import timezone

from baseclasses.typing import SessionDataType

# TODO Make universal MontrekDateTime class


def montrek_time(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
) -> timezone.datetime:
    return timezone.make_aware(
        datetime.datetime(year, month, day, hour, minute, second, microsecond),
        timezone=timezone.get_current_timezone(),
    )


def montrek_today() -> timezone.datetime:
    return timezone.now().date()


def montrek_date_string(date: timezone.datetime) -> str:
    return date.strftime("%Y-%m-%d")


def datetime_to_montrek_time(datetime: datetime.datetime) -> timezone.datetime:
    return montrek_time(
        datetime.year,
        datetime.month,
        datetime.day,
        datetime.hour,
        datetime.minute,
        datetime.second,
        datetime.microsecond,
    )


def get_date_range_dates(request) -> Tuple[str, str]:
    default_start_date = montrek_date_string(montrek_today() - timedelta(days=30))
    default_end_date = montrek_date_string(montrek_today())

    start_date_str = request.session.get("start_date", default_start_date)
    end_date_str = request.session.get("end_date", default_end_date)

    return start_date_str, end_date_str


def get_content_type(filename: str) -> str:
    file_extension = filename.split(".")[-1]
    if file_extension == "pdf":
        return "application/pdf"
    if file_extension == "txt":
        return "text/plain"
    if file_extension == "csv":
        return "text/csv"
    if file_extension == "xlsx":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if file_extension == "zip":
        return "application/zip"
    return "application/octet-stream"


class TableMetaSessionDataElement(ABC):
    field: str = ""

    def __init__(self, session_data: SessionDataType, request) -> None:
        self.session_data = session_data
        self.request = request
        self.request_path = request.path

    def process(self):
        self.session_data.update(self.apply_data())
        self.request.session[self.field] = self.session_data.get(self.field, {})

    @abstractmethod
    def apply_data(self) -> SessionDataType: ...

    def _set_data_to_path(self, default: int | str | None) -> SessionDataType:
        data = {}
        if self.field not in self.session_data:
            data[self.field] = {}
        else:
            data[self.field] = self.session_data[self.field]
        if self.request_path not in data[self.field]:
            data[self.field][self.request_path] = default
        return data


class FilterMetaSessionDataElement(TableMetaSessionDataElement):
    field: str = "filter"

    def apply_data(self) -> SessionDataType:
        filter_data = {self.field: self.session_data.pop("filter", {})}

        filter_fields = self.session_data.pop("filter_field", [])
        filter_negates = self.session_data.pop(
            "filter_negate", [""] * len(filter_fields)
        )
        filter_lookups = self.session_data.pop("filter_lookup", [])
        filter_values = self.session_data.pop("filter_value", [""] * len(filter_fields))
        filter_input_data = list(
            zip(filter_fields, filter_negates, filter_lookups, filter_values)
        )
        if len(filter_input_data) > 0:
            filter_data[self.field][self.request_path] = {}
        for (
            filter_field,
            filter_negate,
            filter_lookup,
            filter_value,
        ) in filter_input_data:
            if filter_lookup == "isnull":
                filter_value = True
            if filter_field:
                true_values = ("True", "true", True)
                false_values = ("False", "false", False)
                filter_negate = filter_negate in true_values
                filter_key = f"{filter_field}__{filter_lookup}"
                if filter_lookup == "in":
                    filter_value = filter_value.split(",")
                if filter_value in true_values:
                    filter_value = True
                elif filter_value in false_values:
                    filter_value = False

                filter_data[self.field][self.request_path][filter_key] = {
                    "filter_negate": filter_negate,
                    "filter_value": filter_value,
                }
                filter_data["page"] = [1]
        return filter_data


class PagesMetaSessionDataElement(TableMetaSessionDataElement):
    field: str = "pages"

    def apply_data(self) -> SessionDataType:
        pages_data = {}
        if self.field not in self.session_data:
            pages_data[self.field] = {}
            self.session_data[self.field] = {}
        else:
            pages_data[self.field] = self.session_data[self.field]
        if "page" in self.session_data:
            page = self.session_data["page"]
            pages_data[self.field][self.request_path] = page
        else:
            if self.request_path in self.session_data[self.field]:
                pages_data["page"] = self.session_data[self.field][self.request_path]
        return pages_data


class FilterCountMetaSessionDataElement(TableMetaSessionDataElement):
    field: str = "filter_count"

    def apply_data(self) -> SessionDataType:
        return self._set_data_to_path(default=1)


class PaginateByMetaSessionDataElement(TableMetaSessionDataElement):
    field: str = "paginate_by"

    def apply_data(self) -> SessionDataType:
        session_data = self._set_data_to_path(default=10)
        if session_data["paginate_by"][self.request.path] < 5:
            session_data["paginate_by"][self.request.path] = 5
        session_data["current_paginate_by"] = session_data["paginate_by"][
            self.request.path
        ]
        return session_data


class IsCompactFormatMetaSessionDataElement(TableMetaSessionDataElement):
    field: str = "is_compact_format"

    def apply_data(self) -> SessionDataType:
        session_data = self._set_data_to_path(default=False)
        session_data["current_is_compact_format"] = session_data["is_compact_format"][
            self.request.path
        ]
        return session_data


class OrderFieldMetaSessionDataElement(TableMetaSessionDataElement):
    field: str = "order_fields"

    def apply_data(self) -> SessionDataType:
        session_data = self._set_data_to_path(default=None)
        session_data["order_field"] = session_data["order_fields"][self.request.path]

        return session_data


class TableMetaSessionData:
    meta_session_data_elements: list[type[TableMetaSessionDataElement]] = [
        OrderFieldMetaSessionDataElement,
        FilterMetaSessionDataElement,
        PagesMetaSessionDataElement,
        FilterCountMetaSessionDataElement,
        PaginateByMetaSessionDataElement,
        IsCompactFormatMetaSessionDataElement,
    ]

    def __init__(self, request) -> None:
        self.request = request

    def update_session_data(self, session_data: SessionDataType) -> SessionDataType:
        for element_class in self.meta_session_data_elements:
            element = element_class(session_data, self.request)
            element.process()
            session_data = element.session_data

        return session_data
