from django.utils import timezone
from depot.repositories.depot_table_queries import get_depot_stats

class DepotStats():
    def __init__(self, account_hub_id:int, reference_date: timezone.datetime):
        self.depot_stats = get_depot_stats(account_hub_id, reference_date)

    @property
    def current_value(self):
        return self.depot_stats['current_value']

    @property
    def book_value(self):
        return self.depot_stats['book_value']

    @property
    def performance(self):
        return self.depot_stats['performance']

