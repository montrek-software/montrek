from django.db import models
from django.db.models import OuterRef, Subquery
from baseclasses.repositories.subquery_builder import SubqueryBuilder
from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from showcase.models.sasset_sat_models import SAssetStaticSatellite
from showcase.models.sproduct_sat_models import SProductSatellite
from showcase.models.stransaction_sat_models import STransactionSatellite
from showcase.models.stransaction_hub_models import (
    LinkSTransactionSAsset,
    LinkSTransactionSProduct,
    STransactionHub,
)


class STransactionRepository(MontrekRepository):
    hub_class = STransactionHub
    default_order_fields = ("product_name", "value_date")

    def set_annotations(self):
        self.session_data["start_date"] = timezone.datetime.min
        self.session_data["end_date"] = timezone.datetime.max
        self.add_satellite_fields_annotations(
            STransactionSatellite,
            [
                "transaction_external_identifier",
                "transaction_description",
                "transaction_quantity",
                "transaction_price",
            ],
        )
        self.add_linked_satellites_field_annotations(
            SProductSatellite, LinkSTransactionSProduct, ["product_name"]
        )
        self.add_linked_satellites_field_annotations(
            SAssetStaticSatellite, LinkSTransactionSAsset, ["asset_name"]
        )


class SPositionSubqueryBuilder(SubqueryBuilder):
    def __init__(self, session_data):
        self.session_data = session_data

    def build(self, reference_date: timezone.datetime) -> Subquery:
        return Subquery(
            STransactionRepository(self.session_data)
            .receive()
            .filter(hub__link_stransaction_sproduct=OuterRef("product_id"))
            .filter(hub__link_stransaction_sasset=OuterRef("asset_id"))
            .values("hub__link_stransaction_sproduct", "hub__link_stransaction_sasset")
            .annotate(position_quantity=models.Sum("transaction_quantity"))
            .values("position_quantity")
        )


class SPositionRepository(MontrekRepository):
    hub_class = STransactionHub

    def set_annotations(self):
        self.session_data["start_date"] = timezone.datetime.min
        self.session_data["end_date"] = timezone.datetime.max
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
        self.annotator.annotations["position_quantity"] = SPositionSubqueryBuilder(
            self.session_data
        )
