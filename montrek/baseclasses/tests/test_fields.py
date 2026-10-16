from decimal import Decimal

from django.test import SimpleTestCase

from baseclasses.fields import FractionField
from baseclasses.forms import PercentDecimalFormField


class TestFractionField(SimpleTestCase):
    def setUp(self):
        self.form_field = FractionField().formfield()

    def test_defaults(self):
        field = FractionField()
        self.assertEqual((field.max_digits, field.decimal_places), (9, 6))
        self.assertTrue(field.null)
        self.assertTrue(field.blank)

    def test_form_field_takes_percent_and_returns_fraction(self):
        self.assertIsInstance(self.form_field, PercentDecimalFormField)
        self.assertEqual(self.form_field.clean("8.5"), Decimal("0.085"))
        self.assertIsNone(self.form_field.clean(""))

    def test_form_field_shows_percent(self):
        self.assertEqual(self.form_field.prepare_value(Decimal("0.085000")), "8.5")

    def test_german_form_field_class_is_replaced(self):
        form_field = FractionField().formfield(form_class=object)
        self.assertIsInstance(form_field, PercentDecimalFormField)
