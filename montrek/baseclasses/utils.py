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


class TableMetaSessionData:
    def __init__(self, request) -> None:
        self.request = request

    def update_session_data(self, session_data: SessionDataType) -> SessionDataType:
        session_data.update(self._get_filters(session_data))
        session_data.update(self._get_page_number(session_data))
        session_data.update(self._get_filter_form_count(session_data))
        self.request.session["filter"] = session_data.get("filter", {})
        self.request.session["pages"] = session_data.get("pages", {})
        self.request.session["filter_count"] = session_data.get("filter_count", {})
        return session_data

    def _get_filters(self, session_data):
        request_path = self.request.path
        filter_data = {"filter": session_data.pop("filter", {})}

        filter_fields = session_data.pop("filter_field", [])
        filter_negates = session_data.pop("filter_negate", [""] * len(filter_fields))
        filter_lookups = session_data.pop("filter_lookup", [])
        filter_values = session_data.pop("filter_value", [""] * len(filter_fields))
        filter_input_data = list(
            zip(filter_fields, filter_negates, filter_lookups, filter_values)
        )
        if len(filter_input_data) > 0:
            filter_data["filter"][request_path] = {}
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
                filter_lookup = filter_lookup
                filter_value = filter_value
                filter_key = f"{filter_field}__{filter_lookup}"
                if filter_lookup == "in":
                    filter_value = filter_value.split(",")
                if filter_value in true_values:
                    filter_value = True
                elif filter_value in false_values:
                    filter_value = False

                filter_data["filter"][request_path][filter_key] = {
                    "filter_negate": filter_negate,
                    "filter_value": filter_value,
                }
        return filter_data

    def _get_page_number(self, session_data):
        request_path = self.request.path
        pages_data = {}
        if "pages" not in session_data:
            pages_data["pages"] = {}
            session_data["pages"] = {}
        else:
            pages_data["pages"] = session_data["pages"]
        if "page" in session_data:
            page = session_data["page"]
            pages_data["pages"][request_path] = page
        else:
            if request_path in session_data["pages"]:
                pages_data["page"] = session_data["pages"][request_path]
        return pages_data

    def _get_filter_form_count(self, session_data):
        request_path = self.request.path
        cfield = "filter_count"
        count_data = {}
        if cfield not in session_data:
            count_data[cfield] = {}
        else:
            count_data[cfield] = session_data[cfield]
        if request_path not in count_data[cfield]:
            count_data[cfield][request_path] = 1
        return count_data
