import csv
from django.views.generic.base import HttpResponse

from django.views.generic.list import QuerySet


class MontrekListManager:
    def export_queryset_to_csv(
        self, queryset: QuerySet, fields: list[str], response: HttpResponse
    ):
        writer = csv.writer(response)
        writer.writerow(fields)
        for row in queryset.values():
            values = []
            for field in fields:
                if field in row:
                    values.append(row[field])
                else:
                    values.append(None)
            writer.writerow(values)
        return response
