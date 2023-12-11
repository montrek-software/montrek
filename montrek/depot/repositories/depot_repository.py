from django.db.models import OuterRef, Subquery, Sum, ExpressionWrapper, F, DecimalField
from baseclasses.repositories.montrek_repository import MontrekRepository
from asset.models import AssetHub, AssetStaticSatellite, AssetLiquidSatellite, AssetTimeSeriesSatellite
from transaction.repositories.transaction_repository import TransactionRepository
from currency.repositories.currency_repository import CurrencyRepository


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
        self.add_last_ts_satellite_fields_annotations(
            AssetTimeSeriesSatellite,
            ["price", "value_date"],
            self.reference_date,
        )
        self._currency_values()
        self._total_nominal_and_book_value()
        self._calculated_fields()
        self._account_fields()
        return self.build_queryset()

    def transaction_table_subquery(self):
        return (
            TransactionRepository(self.request)
            .get_queryset_with_account()
            .filter(
                link_transaction_asset=OuterRef("pk"),
                transaction_date__lte=self.session_end_date,
            )
        )

    def currency_table_subquery(self):
        return (
            CurrencyRepository(self.request)
            .std_queryset()
            .filter(
                link_currency_asset=OuterRef("pk"),
            )
        )

    def _total_nominal_and_book_value(self):
        for tr_field, dp_field in (
            ("transaction_amount", "total_nominal"),
            (
                "transaction_value",
                "book_value",
            ),
        ):
            transaction_sq = Subquery(
                self.transaction_table_subquery()
                .values("link_transaction_asset")
                .annotate(**{dp_field: Sum(tr_field)})
                .values(dp_field)
            )
            self.annotations[dp_field] = transaction_sq

    def _account_fields(self):
        account_sq = Subquery(
            self.transaction_table_subquery()
            .values("account_id")[:1]
        )
        self.annotations["account_id"] = account_sq


    def _currency_values(self):
        for currency_field in ["ccy_code", "fx_rate"]:
            currency_sq = Subquery(
                self.currency_table_subquery().values(currency_field)
            )
            self.annotations[currency_field] = currency_sq
        currency_sq = Subquery(
            self.currency_table_subquery().values("id")
        )
        self.annotations["ccy_id"] = currency_sq

    def _calculated_fields(self):
        self.annotations['book_price'] = ExpressionWrapper(
                F("book_value") / F("total_nominal") * F("fx_rate"), output_field=DecimalField()
            )
        self.annotations['value'] = ExpressionWrapper(
                F("price") * F("total_nominal") * F("fx_rate"), output_field=DecimalField()
            )
        self.annotations['profit_loss'] = ExpressionWrapper(
                F("value") - F("book_value"), output_field=DecimalField()
            )
        self.annotations['performance'] = ExpressionWrapper(
                F("profit_loss") / F("book_value"), output_field=DecimalField()
            )
