from django.test import TestCase
from django.utils import timezone
from asset.tests.factories import asset_factories
from asset.models import AssetTimeSeriesSatellite
from baseclasses.repositories import db_helper


class TestAssetModels(TestCase):
    def test_update_one_asset_time_series(self):
        reference_date = timezone.datetime(2023, 10, 28, tzinfo=timezone.utc)
        ts_1 = asset_factories.AssetTimeSeriesSatelliteFactory(
            value_date=reference_date, price=100
        )
        ts_2 = asset_factories.AssetTimeSeriesSatelliteFactory(
            value_date=reference_date, price=200
        )
        db_helper.new_satellite_entry(
            AssetTimeSeriesSatellite,
            ts_1.hub_entity,
            price=120,
            value_date=reference_date,
        )
        test_ts_1 = db_helper.select_satellite(
            ts_1.hub_entity,
            AssetTimeSeriesSatellite,
        )
        test_ts_2 = db_helper.select_satellite(
            ts_2.hub_entity,
            AssetTimeSeriesSatellite,
        )
        self.assertEqual(test_ts_1.price, 120)
        self.assertEqual(test_ts_2.price, 200)
        self.assertGreater(test_ts_1.created_at, ts_1.created_at)
        self.assertEqual(test_ts_2.created_at, ts_2.created_at)
        self.assertGreater(test_ts_1.state_date_start, timezone.make_aware(timezone.datetime.min))
        self.assertEqual(test_ts_2.state_date_start, timezone.make_aware(timezone.datetime.min))
        self.assertEqual(test_ts_2.state_date_end, timezone.make_aware(timezone.datetime.max))
