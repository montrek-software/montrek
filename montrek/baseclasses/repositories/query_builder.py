from django.db.models import QuerySet, Q
from django.utils import timezone


class QueryBuilder:
    def __init__(self, model, annotator):
        self.model = model
        self.annotator = annotator

    def build_queryset(self, reference_date: timezone.datetime) -> QuerySet:
        query = self.model.objects.annotate(**self.annotator.annotations).filter(
            Q(state_date_start__lte=reference_date),
            Q(state_date_end__gt=reference_date),
        )
        return query
