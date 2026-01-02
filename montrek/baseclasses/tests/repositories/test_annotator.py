from django.test import TestCase
from django.db import models
from django.db.models import CharField, ExpressionWrapper, IntegerField, Subquery, Value
from django.utils import timezone

from baseclasses.repositories.annotator import (
    Annotator,
    FieldProjection,
    SatelliteAlias,
)
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
# Dummy hub
# ----------------------------------------------------------------------


class DummyHub(MontrekHubABC):
    class Meta:
        abstract = True


# ----------------------------------------------------------------------
# Dummy satellites
# ----------------------------------------------------------------------


class StaticSatellite(MontrekSatelliteBaseABC):
    is_timeseries = False

    field_static = models.CharField(max_length=50)

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


# ----------------------------------------------------------------------
# Dummy link
# ----------------------------------------------------------------------


class DummyLink(MontrekManyToManyLinkABC):
    class Meta:
        abstract = True


# ----------------------------------------------------------------------
# Dummy subquery builders
# ----------------------------------------------------------------------


class DummyScalarSubqueryBuilder(SubqueryBuilder):
    def __init__(self, *, satellite_class):
        self.satellite_class = satellite_class

    def build(self, reference_date):
        raise AssertionError("build() must not be called")

    def build_subquery(self, alias_name: str, field: str) -> ExpressionWrapper:
        # Pure ORM expression. No models. No DB. No managers.
        return ExpressionWrapper(
            Value("dummy"),
            output_field=CharField(),
        )


class DummyReverseLinkedBuilder(ReverseLinkedSatelliteSubqueryBuilder):
    def build(self, reference_date):
        return Subquery(StaticSatellite.objects.values("field_static")[:1])


class StubAnnotationBuilder(SubqueryBuilder):
    def __init__(self):
        self.called_with = None

    def build(self, reference_date):
        # Record the call for verification if needed
        self.called_with = reference_date

        # Return a safe, ORM-free expression
        return ExpressionWrapper(
            Value(1),
            output_field=IntegerField(),
        )


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------


class TestAnnotator(TestCase):
    def test_scalar_satellite_creates_alias_and_field_projection(self):
        annotator = Annotator(DummyHub)

        annotator.subquery_builder_to_annotations(
            fields=["field_static"],
            satellite_class=StaticSatellite,
            subquery_builder=DummyScalarSubqueryBuilder,
        )

        # Alias created
        self.assertEqual(len(annotator.satellite_aliases), 1)
        alias = annotator.satellite_aliases[0]

        self.assertIsInstance(alias, SatelliteAlias)
        self.assertEqual(alias.alias_name, "staticsatellite__sat")
        self.assertIsInstance(alias.subquery_builder, DummyScalarSubqueryBuilder)

        # Field projection created via build_subquery
        self.assertEqual(len(annotator.field_projections), 1)
        self.assertEqual("field_static", annotator.field_projections[0].field)

        # Satellite registered
        self.assertIn(StaticSatellite, annotator.annotated_satellite_classes)

    def test_ts_sum_satellite_uses_ts_sum_builder(self):
        annotator = Annotator(DummyHub)

        annotator.subquery_builder_to_annotations(
            fields=["field_ts"],
            satellite_class=TSSatellite,
            subquery_builder=DummyScalarSubqueryBuilder,
            ts_agg_func="sum",
        )

        # No alias for TS sum
        self.assertEqual(annotator.satellite_aliases, [])

        # Annotation created
        self.assertIn("field_ts", annotator.annotations)
        self.assertIsInstance(
            annotator.annotations["field_ts"],
            TSSumFieldSubqueryBuilder,
        )

        # No scalar projections
        self.assertEqual(annotator.field_projections, [])

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

    def test_rename_field_updates_all_maps(self):
        annotator = Annotator(DummyHub)

        annotator.annotations["old"] = DummyScalarSubqueryBuilder(
            satellite_class=StaticSatellite
        )
        annotator.field_projections.append(
            FieldProjection(
                field="old",
                outfield="old",
                satellite_alias=SatelliteAlias(
                    alias_name="dummy",
                    subquery_builder=DummyScalarSubqueryBuilder(
                        satellite_class=StaticSatellite
                    ),
                ),
            )
        )

        annotator.rename_field("old", "new")

        self.assertNotIn("old", annotator.annotations)
        self.assertIn("new", annotator.annotations)

        self.assertEqual("old", annotator.field_projections[0].field)
        self.assertEqual("new", annotator.field_projections[0].outfield)

        # Optional sanity check: value was preserved, not recreated
        self.assertIsInstance(
            annotator.field_projections[
                0
            ].satellite_alias.subquery_builder.build_subquery("dummy", "old"),
            ExpressionWrapper,
        )

    def test_build_calls_build_on_annotation_builders(self):
        annotator = Annotator(DummyHub)

        builder = StubAnnotationBuilder()
        annotator.annotations = {"x": builder}

        result = annotator.build(timezone.now())

        self.assertIn("x", result)
        self.assertIsInstance(result["x"], ExpressionWrapper)
