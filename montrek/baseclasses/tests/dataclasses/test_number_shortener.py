from django.test import TestCase, override_settings

from baseclasses.dataclasses import number_shortener as ns
from montrek.utils import SystemFormatting


class TestNumberShortener(TestCase):
    def test_no_shortening(self):
        test_shortener = ns.NoShortening()
        self.assertEqual(test_shortener.shorten(1234.5678, 4), "1,234.5678")
        self.assertEqual(test_shortener.shorten(1234, 0), "1,234")
        self.assertEqual(test_shortener.shorten(-1234.5678, 2), "-1,234.57")

    def test_kilo_shortening(self):
        test_shortener = ns.KiloShortening()
        self.assertEqual(test_shortener.shorten(1234.5678e3, 4), "1,234.5678k")
        self.assertEqual(test_shortener.shorten(1234e3, 0), "1,234k")
        self.assertEqual(test_shortener.shorten(-1234.5678e3, 2), "-1,234.57k")

    def test_million_shortening(self):
        test_shortener = ns.MillionShortening()
        self.assertEqual(test_shortener.shorten(1234.5678e6, 4), "1,234.5678mn")
        self.assertEqual(test_shortener.shorten(1234e6, 0), "1,234mn")
        self.assertEqual(test_shortener.shorten(-1234.5678e6, 2), "-1,234.57mn")

    def test_billion_shortening(self):
        test_shortener = ns.BillionShortening()
        self.assertEqual(test_shortener.shorten(1234.5678e9, 4), "1,234.5678bn")
        self.assertEqual(test_shortener.shorten(1234e9, 0), "1,234bn")
        self.assertEqual(test_shortener.shorten(-1234.5678e9, 2), "-1,234.57bn")


@override_settings(NUMBER_FORMATTING=SystemFormatting.DE)
class TestNumberShortenerGerman(TestCase):
    def test_no_shortening_de(self):
        test_shortener = ns.NoShortening()
        self.assertEqual(test_shortener.shorten(1234.5678, 4), "1.234,5678")
        self.assertEqual(test_shortener.shorten(1234, 0), "1.234")
        self.assertEqual(test_shortener.shorten(-1234.5678, 2), "-1.234,57")

    def test_kilo_shortening_de(self):
        test_shortener = ns.KiloShortening()
        self.assertEqual(test_shortener.shorten(1234.5678e3, 4), "1.234,5678k")
        self.assertEqual(test_shortener.shorten(1234e3, 0), "1.234k")
        self.assertEqual(test_shortener.shorten(-1234.5678e3, 2), "-1.234,57k")

    def test_million_shortening_de(self):
        test_shortener = ns.MillionShortening()
        self.assertEqual(test_shortener.shorten(1234.5678e6, 4), "1.234,5678mn")
        self.assertEqual(test_shortener.shorten(-1234.5678e6, 2), "-1.234,57mn")

    def test_billion_shortening_de(self):
        test_shortener = ns.BillionShortening()
        self.assertEqual(test_shortener.shorten(1234.5678e9, 4), "1.234,5678bn")
        self.assertEqual(test_shortener.shorten(-1234.5678e9, 2), "-1.234,57bn")
