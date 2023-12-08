from django.db.models import OuterRef, Subquery, Sum
from baseclasses.repositories.montrek_repository import MontrekRepository
from asset.models import AssetHub, AssetStaticSatellite, AssetLiquidSatellite
from transaction.repositories.transaction_repository import TransactionRepository


class DepotRepository(MontrekRepository):
    hub_class = AssetHub

    def std_queryset(self):
        self.add_satellite_fields_annotations(
            AssetStaticSatellite,
            ["asset_name", "asset_type"],
            self.reference_date,
        )
        self.add_satellite_fields_annotations(
            AssetLiquidSatellite,
            ["asset_isin", "asset_wkn"],
            self.reference_date,
        )
        self._total_nominal()
        return self.build_queryset()

    def transaction_table_subquery(self, **kwargs):
        return (
            TransactionRepository(self.request)
            .std_queryset()
            .filter(
                link_transaction_asset=OuterRef("pk"),
                transaction_date__lte=self.session_end_date,
            )
        )

    def _total_nominal(self):
        transaction_sq = Subquery(
            self.transaction_table_subquery()
            .values("link_transaction_asset")
            .annotate(total_nominal=Sum("transaction_value"))
            .values("total_nominal")
        )
        self.annotations["total_nominal"] = transaction_sq
