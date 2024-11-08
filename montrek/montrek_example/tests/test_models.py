from django.test import TestCase
from django.db.models import Subquery, OuterRef
from montrek_example.models import SatC1, SatTSC3, HubC, CHubValueDate, SatTSC2
from montrek_example.tests.factories.montrek_example_factories import (
    SatTSC2Factory,
    SatTSC3Factory,
    SatC1Factory,
)


class TestMontrekSatellite(TestCase):
    def test_value_fields_with_generated_field(self):
        test_model_class = SatTSC3
        value_fields = test_model_class.get_value_fields()
        self.assertEqual(
            [field.name for field in value_fields],
            ["comment", "value_date", "field_tsc3_int", "field_tsc3_str"],
        )

    def annotations(self):
        return {
            "field_c1_str": Subquery(
                HubC.objects.filter(pk=OuterRef("hub"))
                .annotate(
                    **{
                        "field_c1_str": Subquery(
                            SatC1.objects.filter(hub_entity=OuterRef("pk")).values(
                                "field_c1_str"
                            )
                        )
                    }
                )
                .values("field_c1_str")
            ),
            "field_tsc2_float": Subquery(
                SatTSC2.objects.filter(hub_value_date=OuterRef("pk")).values(
                    "field_tsc2_float"
                )
            ),
            "field_tsc3_int": Subquery(
                SatTSC3.objects.filter(hub_value_date=OuterRef("pk")).values(
                    "field_tsc3_int"
                )
            ),
        }

    def test_ts_satellite_concept__single_entry(self):
        tsc2_fac = SatTSC2Factory()
        annotations = self.annotations()
        query = CHubValueDate.objects.annotate(**annotations)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac.field_tsc2_float)
        self.assertEqual(
            query.first().value_date, tsc2_fac.hub_value_date.value_date.date()
        )

    def test_ts_satellite_concept__two_hubs(self):
        tsc2_fac1 = SatTSC2Factory(field_tsc2_float=10)
        tsc2_fac2 = SatTSC2Factory(field_tsc2_float=20)
        annotations = self.annotations()
        query = CHubValueDate.objects.annotate(**annotations)
        self.assertEqual(query.count(), 2)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac1.field_tsc2_float)
        self.assertEqual(query.last().field_tsc2_float, tsc2_fac2.field_tsc2_float)

    def test_ts_satellite_concept__two_dates(self):
        tsc2_fac1 = SatTSC2Factory(field_tsc2_float=10)
        tsc2_fac2 = SatTSC2Factory(
            field_tsc2_float=20,
            hub_value_date__hub=tsc2_fac1.hub_value_date.hub,
        )
        annotations = self.annotations()
        query = CHubValueDate.objects.annotate(**annotations)
        self.assertEqual(query.count(), 2)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac1.field_tsc2_float)
        self.assertEqual(query.last().field_tsc2_float, tsc2_fac2.field_tsc2_float)
        self.assertEqual(
            query.first().value_date, tsc2_fac1.hub_value_date.value_date.date()
        )
        self.assertEqual(
            query.last().value_date, tsc2_fac2.hub_value_date.value_date.date()
        )

    def test_ts_satellite_concept__with_sat(self):
        tsc2_fac1 = SatTSC2Factory(field_tsc2_float=10)
        c_sat = SatC1Factory(
            hub_entity=tsc2_fac1.hub_value_date.hub, field_c1_str="hallo"
        )
        annotations = self.annotations()
        query = CHubValueDate.objects.annotate(**annotations)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac1.field_tsc2_float)
        self.assertEqual(
            query.first().value_date, tsc2_fac1.hub_value_date.value_date.date()
        )
        self.assertEqual(query.first().field_c1_str, c_sat.field_c1_str)

    def test_ts_satellite_concept__two_ts_sats(self):
        tsc2_fac = SatTSC2Factory(field_tsc2_float=10)
        c_sat1 = SatC1Factory(
            hub_entity=tsc2_fac.hub_value_date.hub, field_c1_str="hallo"
        )
        tsc3_fac = SatTSC3Factory(
            field_tsc3_int=20, hub_value_date=tsc2_fac.hub_value_date
        )
        annotations = self.annotations()
        query = CHubValueDate.objects.annotate(**annotations)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac.field_tsc2_float)
        self.assertEqual(
            query.first().value_date, tsc2_fac.hub_value_date.value_date.date()
        )
        self.assertEqual(query.first().field_c1_str, c_sat1.field_c1_str)
        self.assertEqual(query.first().field_tsc3_int, tsc3_fac.field_tsc3_int)
