from django.test import TestCase
from django.db import models
from django.db.models import Subquery
from django.utils import timezone

from baseclasses.repositories.annotator import Annotator
from baseclasses.repositories.subquery_builder import (
    SubqueryBuilder,
    TSSumFieldSubqueryBuilder,
    ReverseLinkedSatelliteSubqueryBuilder,
)
from baseclasses.models import (
    MontrekHubABC,
    MontrekSatelliteBaseABC,
    MontrekManyToManyLinkABC,
)


# ----------------------------------------------------------------------
# Mock / stub infrastructure
# ----------------------------------------------------------------------


class DummyHub(MontrekHubABC):
    class Meta:
        abstract = True


class StaticSatellite(MontrekSatelliteBaseABC):
    is_timeseries = False

    field_static = models.CharField(max_length=50)
    objects = models.Manager()

    @classmethod
    def get_related_hub_class(cls):
        return DummyHub

    @classmethod
    def get_value_fields(cls):
        return [cls._meta.get_field("field_static")]

    class Meta:
        abstract = True


class TSSatellite(MontrekSatelliteBaseABC):
    is_timeseries = True

    field_ts = models.FloatField()

    @classmethod
    def get_related_hub_class(cls):
        return DummyHub

    @classmethod
    def get_value_fields(cls):
        return [cls._meta.get_field("field_ts")]

    class Meta:
        abstract = True


class DummyLink(MontrekManyToManyLinkABC):
    class Meta:
        abstract = True


class DummySubqueryBuilder(SubqueryBuilder):
    def __init__(self, *args, **kwargs):
        pass

    def build(self, reference_date):
        return Subquery(StaticSatellite.objects.values("field_static")[:1])


class DummyReverseLinkedBuilder(ReverseLinkedSatelliteSubqueryBuilder):
    def build(self, reference_date):
        return Subquery(StaticSatellite.objects.values("field_static")[:1])


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------


class TestAnnotator(TestCase):
    def test_scalar_satellite_creates_alias_and_projection(self):
        annotator = Annotator(DummyHub)

        annotator.subquery_builder_to_annotations(
            fields=["field_static"],
            satellite_class=StaticSatellite,
            subquery_builder=DummySubqueryBuilder,
        )

        # Alias created
        self.assertEqual(len(annotator.satellite_aliases), 1)
        alias = annotator.satellite_aliases[0]
        self.assertEqual(alias.alias_name, "staticsatellite__sat")

        # Field projection created
        self.assertIn("field_static", annotator.field_projections)
        self.assertIsInstance(annotator.field_projections["field_static"], Subquery)

        # Satellite registered
        self.assertIn(StaticSatellite, annotator.annotated_satellite_classes)

    def test_ts_sum_satellite_uses_ts_sum_builder(self):
        annotator = Annotator(DummyHub)

        annotator.subquery_builder_to_annotations(
            fields=["field_ts"],
            satellite_class=TSSatellite,
            subquery_builder=DummySubqueryBuilder,
            ts_agg_func="sum",
        )

        # No alias for TS sum
        self.assertEqual(annotator.satellite_aliases, [])

        # Annotation created using TS sum builder
        self.assertIn("field_ts", annotator.annotations)
        self.assertIsInstance(
            annotator.annotations["field_ts"],
            TSSumFieldSubqueryBuilder,
        )

        # No field projections
        self.assertEqual(annotator.field_projections, {})

        # Satellite registered
        self.assertIn(TSSatellite, annotator.annotated_satellite_classes)

    def test_linked_satellite_creates_annotation_and_link_registration(self):
        annotator = Annotator(DummyHub)

        annotator.subquery_builder_to_annotations(
            fields=["field_static"],
            satellite_class=StaticSatellite,
            subquery_builder=DummyReverseLinkedBuilder,
            link_class=DummyLink,
            agg_func="string_concat",
        )

        # Annotation created
        self.assertIn("field_static", annotator.annotations)
        self.assertIsInstance(
            annotator.annotations["field_static"],
            ReverseLinkedSatelliteSubqueryBuilder,
        )

        # Link class registered
        self.assertIn(DummyLink, annotator.annotated_link_classes)

        # Satellite registered
        self.assertIn(StaticSatellite, annotator.annotated_satellite_classes)

        # Field type overridden to CharField
        field = annotator.field_type_map["field_static"]
        self.assertIsInstance(field, models.CharField)

    def test_rename_field_updates_annotations_and_projections(self):
        annotator = Annotator(DummyHub)

        annotator.annotations["old"] = DummySubqueryBuilder()
        annotator.field_projections["old"] = Subquery(
            StaticSatellite.objects.values("field_static")[:1]
        )

        annotator.rename_field("old", "new")

        self.assertNotIn("old", annotator.annotations)
        self.assertIn("new", annotator.annotations)

        self.assertNotIn("old", annotator.field_projections)
        self.assertIn("new", annotator.field_projections)

    def test_build_calls_subquery_build(self):
        annotator = Annotator(DummyHub)

        builder = DummySubqueryBuilder()
        annotator.annotations["x"] = builder

        result = annotator.build(timezone.now())

        self.assertIn("x", result)
        self.assertIsInstance(result["x"], Subquery)
