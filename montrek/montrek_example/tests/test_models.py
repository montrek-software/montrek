from django.test import TestCase
from montrek_example.models import SatA3, SatTSC3, HubA


class TestMontrekSatellite(TestCase):
    def test_value_fields_with_generated_field(self):
        test_model_class = SatTSC3
        value_fields = test_model_class.get_value_fields()
        self.assertEqual(
            [field.name for field in value_fields],
            ["comment", "value_date", "field_tsc3_int", "field_tsc3_str"],
        )

    def test_json_field__from_dict(self):
        test_dict = {"key": "value"}
        test_hub = HubA.objects.create()
        SatA3(hub_entity=test_hub, field_a3_str="test", field_a3_json=test_dict).save()
        test_object = SatA3.objects.get(hub_entity=test_hub)
        self.assertEqual(test_object.field_a3_json, test_dict)

    def test_json_field__from_str(self):
        test_str = '{"key": "value"}'
        test_hub = HubA.objects.create()
        SatA3(hub_entity=test_hub, field_a3_str="test", field_a3_json=test_str).save()
        test_object = SatA3.objects.get(hub_entity=test_hub)
        self.assertEqual(test_object.field_a3_json, {"key": "value"})
