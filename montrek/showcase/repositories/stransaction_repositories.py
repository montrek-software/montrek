from baseclasses.repositories.montrek_repository import MontrekRepository
from django.utils import timezone

from showcase.models.sasset_sat_models import SAssetStaticSatellite
from showcase.models.sproduct_sat_models import SProductSatellite
from showcase.models.stransaction_hub_models import (
    LinkSTransactionSAsset,
    LinkSTransactionSProduct,
    STransactionHub,
)
from showcase.models.stransaction_sat_models import STransactionSatellite
from showcase.repositories.sproduct_repositories import SProductRepository

from baseclasses.repositories.subquery_builder import SubqueryBuilder
from django.db import models
from django.db.models import OuterRef, Subquery, QuerySet

from showcase.models.sasset_hub_models import SAssetHub


class STransactionRepository(MontrekRepository):
    hub_class = STransactionHub
    default_order_fields = ("product_name", "transaction_date")

    def set_annotations(self):
        self.session_data["start_date"] = timezone.datetime.min
        self.session_data["end_date"] = timezone.datetime.max
        self.add_satellite_fields_annotations(
            STransactionSatellite,
            [
                "transaction_date",
                "transaction_external_identifier",
                "transaction_description",
                "transaction_quantity",
                "transaction_price",
            ],
        )
        self.add_linked_satellites_field_annotations(
            SProductSatellite,
            LinkSTransactionSProduct,
            ["hub_entity_id", "product_name"],
            rename_field_map={"hub_entity_id": "product_id"},
        )
        self.add_linked_satellites_field_annotations(
            SAssetStaticSatellite,
            LinkSTransactionSAsset,
            ["hub_entity_id", "asset_name"],
            rename_field_map={"hub_entity_id": "asset_id"},
        )


class SProductSTransactionRepository(STransactionRepository):
    def receive(self, apply_filter: bool = True) -> QuerySet:
        product_repo = SProductRepository(self.session_data)
        product_hub = product_repo.get_hub_by_id(self.session_data["pk"])
        return super().receive().filter(hub__link_stransaction_sproduct=product_hub)


class SProductSPositionSubqueryBuilder(SubqueryBuilder):
    def __init__(self, session_data):
        self.session_data = session_data

    def build(self, reference_date: timezone.datetime) -> Subquery:
        product_repo = SProductRepository(self.session_data)
        product_hub = product_repo.get_hub_by_id(self.session_data["pk"])
        sq = Subquery(
            STransactionRepository(self.session_data)
            .receive()
            .order_by()
            .filter(hub__link_stransaction_sasset=OuterRef("pk"))
            .filter(hub__link_stransaction_sproduct=product_hub)
            .values("asset_id")
            .annotate(position_quantity=models.Sum("transaction_quantity"))
            .values("position_quantity")
        )
        return sq


class SProductSPositionRepository(MontrekRepository):
    hub_class = SAssetHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(SAssetStaticSatellite, ["asset_name"])
        self.add_satellite_fields_annotations(SAssetStaticSatellite, ["asset_isin"])
        self.annotator.annotations[
            "position_quantity"
        ] = SProductSPositionSubqueryBuilder(self.session_data)

    def receive(self, apply_filter: bool = True) -> QuerySet:
        qs = super().receive(apply_filter)
        qs = qs.filter(position_quantity__isnull=False)
        return qs
