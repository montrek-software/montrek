from django.test import TestCase
from montrek_example.models import SatTSC3


class TestMontrekSatellite(TestCase):
    def test_value_fields_with_generated_field(self):
        test_model_class = SatTSC3
        value_fields = test_model_class.get_value_fields()
        self.assertEqual(
            [field.name for field in value_fields],
            ["comment", "value_date", "field_tsc3_int", "field_tsc3_str"],
        )
