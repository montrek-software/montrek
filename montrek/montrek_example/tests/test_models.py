from baseclasses.models import ValueDateList
from django.db.models import OuterRef, Q, Subquery
from django.test import TestCase

from montrek_example.models import (
    CHubValueDate,
    HubC,
    SatC1,
    SatD1,
    SatTSC2,
    SatTSC3,
    SatTSD2,
)
from montrek_example.tests.factories.montrek_example_factories import (
    CHubValueDateFactory,
    DHubValueDateFactory,
    SatC1Factory,
    SatD1Factory,
    SatTSC2Factory,
    SatTSC3Factory,
    SatTSD2Factory,
    ValueDateListFactory,
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
        hub_query = HubC.objects.filter(pk=OuterRef("hub"))
        return {
            "field_c1_str": Subquery(
                hub_query.annotate(
                    **{
                        "field_c1_str": Subquery(
                            SatC1.objects.filter(hub_entity=OuterRef("pk")).values(
                                "field_c1_str"
                            )
                        )
                    }
                ).values("field_c1_str")
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
            "value_date": Subquery(
                ValueDateList.objects.filter(pk=OuterRef("value_date_list")).values(
                    "value_date"
                )
            ),
            "field_d1_str": Subquery(
                hub_query.annotate(
                    **{
                        "field_d1_str": Subquery(
                            SatD1.objects.filter(
                                hub_entity=OuterRef("linkhubchubd__hub_out")
                            ).values("field_d1_str")
                        )
                    }
                ).values("field_d1_str")
            ),
            "field_tsd2_float": Subquery(
                hub_query.annotate(
                    **{
                        "field_tsd2_float": Subquery(
                            SatTSD2.objects.filter(
                                Q(
                                    hub_value_date=OuterRef(
                                        "linkhubchubd__hub_out__hub_value_date"
                                    )
                                )
                                & Q(
                                    hub_value_date__value_date_list=OuterRef(
                                        "hub_value_date__value_date_list"
                                    )
                                )
                            ).values("field_tsd2_float")
                        )
                    }
                ).values("field_tsd2_float")[:1]
            ),
        }

    def test_ts_satellite_concept__single_entry(self):
        tsc2_fac = SatTSC2Factory()
        annotations = self.annotations()
        query = CHubValueDate.objects.annotate(**annotations)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac.field_tsc2_float)
        self.assertEqual(
            query.first().value_date,
            tsc2_fac.hub_value_date.value_date_list.value_date,
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
            query.first().value_date,
            tsc2_fac1.hub_value_date.value_date_list.value_date,
        )
        self.assertEqual(
            query.last().value_date,
            tsc2_fac2.hub_value_date.value_date_list.value_date,
        )

    def test_ts_satellite_concept__with_sat(self):
        tsc2_fac1 = SatTSC2Factory(field_tsc2_float=10)
        c_sat = SatC1Factory(
            hub_entity=tsc2_fac1.hub_value_date.hub, field_c1_str="hallo"
        )
        annotations = self.annotations()
        query = CHubValueDate.objects.annotate(**annotations)
        self.assertEqual(query.count(), 2)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac1.field_tsc2_float)
        self.assertEqual(
            query.first().value_date,
            tsc2_fac1.hub_value_date.value_date_list.value_date,
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
        self.assertEqual(query.count(), 2)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac.field_tsc2_float)
        self.assertEqual(
            query.first().value_date,
            tsc2_fac.hub_value_date.value_date_list.value_date,
        )
        self.assertEqual(query.first().field_c1_str, c_sat1.field_c1_str)
        self.assertEqual(query.first().field_tsc3_int, tsc3_fac.field_tsc3_int)

    def test_ts_satellite_concept__linked_sat(self):
        c_hub_value_date = CHubValueDateFactory.create()
        c_sat1 = SatC1Factory(field_c1_str="hallo", hub_entity=c_hub_value_date.hub)
        d_sat1 = SatD1Factory.create(
            field_d1_str="test",
        )
        c_sat1.hub_entity.link_hub_c_hub_d.add(d_sat1.hub_entity)
        annotations = self.annotations()
        query = CHubValueDate.objects.annotate(**annotations)
        self.assertEqual(query.count(), 2)
        self.assertEqual(query.first().field_c1_str, c_sat1.field_c1_str)
        self.assertEqual(query.first().field_d1_str, d_sat1.field_d1_str)

    def test_ts_satellite_concept__linked_ts_sat(self):
        value_date_list = ValueDateListFactory()
        c_hub_value_date = CHubValueDateFactory.create(value_date_list=value_date_list)
        d_hub_value_date = DHubValueDateFactory.create(value_date_list=value_date_list)
        d_hub_value_date2 = DHubValueDateFactory.create(hub=d_hub_value_date.hub)
        c_sat = SatTSC2Factory.create(
            hub_value_date=c_hub_value_date, field_tsc2_float=10
        )
        d_sat = SatTSD2Factory.create(
            hub_value_date=d_hub_value_date, field_tsd2_float=20
        )
        SatTSD2Factory.create(field_tsd2_float=30, hub_value_date=d_hub_value_date2)
        c_hub_value_date.hub.link_hub_c_hub_d.add(d_hub_value_date.hub)
        annotations = self.annotations()
        query = CHubValueDate.objects.annotate(**annotations)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().field_tsc2_float, c_sat.field_tsc2_float)
        self.assertEqual(query.first().field_tsd2_float, d_sat.field_tsd2_float)

    def test_ts_satellite_concept__two_ts_sats_different_dates(self):
        tsc2_fac1 = SatTSC2Factory(field_tsc2_float=10)
        c_sat1 = SatC1Factory(
            hub_entity=tsc2_fac1.hub_value_date.hub, field_c1_str="hallo"
        )
        tsc3_fac = SatTSC3Factory(
            field_tsc3_int=20, hub_value_date=tsc2_fac1.hub_value_date
        )
        tsc3_fac_2 = SatTSC3Factory(
            field_tsc3_int=30,
        )
        c_sat2 = SatC1Factory(
            hub_entity=tsc3_fac_2.hub_value_date.hub, field_c1_str="wallo"
        )
        annotations = self.annotations()
        query = CHubValueDate.objects.annotate(**annotations)
        self.assertEqual(query.count(), 4)
        result_1 = query.first()
        result_2 = query[2]
        self.assertEqual(result_1.field_tsc2_float, tsc2_fac1.field_tsc2_float)
        self.assertEqual(
            result_1.value_date,
            tsc2_fac1.hub_value_date.value_date_list.value_date,
        )
        self.assertEqual(result_1.field_c1_str, c_sat1.field_c1_str)
        self.assertEqual(result_1.field_tsc3_int, tsc3_fac.field_tsc3_int)
        self.assertEqual(result_2.field_tsc2_float, None)
        self.assertEqual(
            result_2.value_date,
            tsc3_fac_2.hub_value_date.value_date_list.value_date,
        )
        self.assertEqual(result_2.field_c1_str, c_sat2.field_c1_str)
        self.assertEqual(result_2.field_tsc3_int, tsc3_fac_2.field_tsc3_int)
