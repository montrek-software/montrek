from decimal import Decimal
from depot.tests.repositories.test_depot_table_queries import TestDepotTable
from depot.managers.depot_stats import DepotStats
from baseclasses.utils import montrek_time


class TestDepotStats(TestDepotTable):
    def test_depot_stats(self):
        test_depot_stats = DepotStats(self.account.id,self.reference_date)
        self.assertAlmostEqual(test_depot_stats.current_value, Decimal(7235.1))
        self.assertAlmostEqual(test_depot_stats.book_value, Decimal(8500))
        self.assertAlmostEqual(test_depot_stats.performance, Decimal(-0.148811764705882))
        
