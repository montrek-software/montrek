from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses.repositories.subquery_builder import SubqueryBuilder
from data_import.api_import.repositories.api_data_import_registry_repositories import (
    ApiDataImportRegistryRepository,
)
from file_export.repositories.file_export_registry_repository import (
    FileExportRegistryRepositoryABC,
)
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepositoryABC,
)
from django.db.models import Case, IntegerField, QuerySet, Value, When
from django.utils import timezone

from montrek_example.models import example_models as me_models
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository


class _QuerysetAwareSubqueryBuilder(SubqueryBuilder):
    """
    Test-only builder that demonstrates the queryset parameter on build().

    When the queryset is forwarded, it inspects the intermediate queryset to
    collect ``field_a1_int`` per ``hub_id`` in Python and embeds the doubled
    values as explicit per-row literals in a Case expression.

    Returns ``None`` for every row when ``queryset`` is ``None`` (the current
    behaviour before the framework change), and the correct per-row value once
    ``QueryBuilder`` and ``Annotator`` forward the queryset.
    """

    def build(
        self,
        reference_date: timezone.datetime,
        queryset: QuerySet | None = None,
    ) -> Case | Value:
        if queryset is None:
            return Value(None, output_field=IntegerField())

        id_to_doubled = {
            row["hub_id"]: row["field_a1_int"] * 2
            for row in queryset.values("hub_id", "field_a1_int")
            if row["field_a1_int"] is not None
        }
        return Case(
            *(
                When(hub_id=hub_id, then=Value(doubled))
                for hub_id, doubled in id_to_doubled.items()
            ),
            default=Value(None),
            output_field=IntegerField(),
        )


class HubAQuerysetAwareRepository(MontrekRepository):
    """Repository used to verify that ``QueryBuilder`` forwards the intermediate
    queryset to ``SubqueryBuilder.build()``, enabling Python-side computations
    over field-projected rows."""

    hub_class = me_models.HubA

    def set_annotations(self) -> None:
        self.add_satellite_fields_annotations(me_models.SatA1, ["field_a1_int"])
        self.annotator.annotations["field_a1_int_doubled"] = (
            _QuerysetAwareSubqueryBuilder()
        )


class HubARepository(MontrekRepository):
    hub_class = me_models.HubA
    default_order_fields = ("hub_id",)
    display_field_names = {
        "field_a2_float": "Renamed Label",
        "link_hub_a_hub_c": "Renamed Link Label",
    }

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA1,
            [
                "field_a1_int",
                "field_a1_str",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatA2,
            [
                "field_a2_float",
                "field_a2_str",
            ],
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatB1,
            me_models.LinkHubAHubB,
            ["field_b1_str", "field_b1_date"],
        )

    def get_hub_b_objects(self):
        return HubBRepository().receive()

    def get_hub_c_objects(self):
        return HubCRepository().receive()

    def test_queryset_1(self):
        self.add_satellite_fields_annotations(
            me_models.SatA1,
            [
                "field_a1_int",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatA2,
            [
                "field_a2_float",
            ],
        )
        return self.receive()


class HubARepository2(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatC1,
            me_models.LinkHubAHubC,
            ["field_c1_str"],
        )


class HubARepository3(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA1,
            [
                "field_a1_str",
            ],
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubCHubD,
            ["field_d1_str"],
            parent_link_classes=(me_models.LinkHubAHubC,),
        )


class HubARepository4(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA4,
            [
                "field_a4_str",
            ],
        )


class HubARepository5(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA5,
            [
                "field_a5_str",
                "secret_field",
            ],
        )


class HubARepository6(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA4,
            [
                "field_a4_str",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatA1,
            ["field_a1_str", "field_a1_int"],
        )


class HubAApiUploadRepository(ApiDataImportRegistryRepository):
    hub_class = me_models.HubAApiUploadRegistryHub
    registry_satellite = me_models.HubAApiUploadRegistryStaticSatellite


class HubAFileUploadRegistryRepository(FileUploadRegistryRepositoryABC):
    hub_class = me_models.HubAFileUploadRegistryHub
    static_satellite_class = me_models.HubAFileUploadRegistryStaticSatellite
    link_file_upload_registry_file_upload_file_class = (
        me_models.LinkHubAFileUploadRegistryFileUploadFile
    )
    link_file_upload_registry_file_log_file_class = (
        me_models.LinkHubAFileUploadRegistryFileLogFile
    )


class HubAJsonRepository(MontrekRepository):
    hub_class = me_models.HubA

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatA3,
            [
                "field_a3_str",
                "field_a3_json",
            ],
        )


class HubAFileExportRegistryRepository(FileExportRegistryRepositoryABC):
    hub_class = me_models.HubAFileExportRegistryHub
    registry_satellite = me_models.HubAFileExportRegistryStaticSatellite


class HubATSLinkedRepository(MontrekRepository):
    """Fetches multiple TS fields from SatTSC3 via the scalar LinkHubAHubC link.

    Used to exercise the ``_build_ts_scalar_alias`` optimization path: both
    fields from the same scalar timeseries linked satellite share a single
    alias subquery that resolves the satellite pk at the matching value_date,
    and each field is then resolved via a cheap pk-lookup projection.
    """

    hub_class = me_models.HubA
    latest_ts = True

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatTSC3,
            me_models.LinkHubAHubC,
            ["field_tsc3_int", "field_tsc3_str"],
        )
