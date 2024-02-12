from django.db.models import QuerySet
from asset.models import AssetHub
from asset.models import AssetStaticSatellite
from asset.models import AssetLiquidSatellite
from asset.models import AssetTimeSeriesSatellite
from asset.models import LinkAssetCurrency
from currency.models import CurrencyStaticSatellite
from currency.models import CurrencyTimeSeriesSatellite
from baseclasses.repositories.montrek_repository import MontrekRepository


class AssetRepository(MontrekRepository):
    hub_class = AssetHub

    def std_queryset(self):
        self.add_satellite_fields_annotations(
            AssetStaticSatellite,
            ["asset_name", "asset_type"],
            self.reference_date,
        )
        self.add_last_ts_satellite_fields_annotations(
            AssetTimeSeriesSatellite,
            ["price", "value_date"],
            self.reference_date,
        )
        self.add_satellite_fields_annotations(
            AssetLiquidSatellite,
            ["asset_isin", "asset_wkn"],
            self.reference_date,
        )
        self.add_linked_satellites_field_annotations(
            CurrencyStaticSatellite,
            LinkAssetCurrency,
            ["ccy_code", "hub_entity_id"],
            self.reference_date,
        )
        self.rename_field("hub_entity_id", "ccy_id")
        self.add_linked_satellites_field_annotations(
            CurrencyTimeSeriesSatellite,
            LinkAssetCurrency,
            ["fx_rate"],
            self.reference_date,
        )
        return self.build_queryset()

    def get_asset_prices(self, asset_id: int) -> QuerySet:
        queryset = AssetTimeSeriesSatellite.objects.filter(
            hub_entity_id=asset_id,
            state_date_start__lte=self.reference_date,
            state_date_end__gte=self.reference_date,
            value_date__lte=self.session_end_date,
            value_date__gte=self.session_start_date,
        ).order_by("value_date")
        return queryset
