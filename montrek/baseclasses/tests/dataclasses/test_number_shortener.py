from django.test import TestCase
from baseclasses.dataclasses import number_shortener as ns


class TestNumberShortener(TestCase):
    def test_no_shortening(self):
        test_shortener = ns.NoShortening()
        self.assertEqual(test_shortener.shorten(1234.5678, ""), "1234.5678")
        self.assertEqual(test_shortener.shorten(1234, ""), "1234")
        self.assertEqual(test_shortener.shorten(-1234.5678, ",.2f"), "-1,234.57")

    def test_kilo_shortening(self):
        test_shortener = ns.KiloShortening()
        self.assertEqual(test_shortener.shorten(1234.5678e3, ""), "1234.5678k")
        self.assertEqual(test_shortener.shorten(1234e3, ""), "1234.0k")
        self.assertEqual(test_shortener.shorten(-1234.5678e3, ",.2f"), "-1,234.57k")

    def test_million_shortening(self):
        test_shortener = ns.MillionShortening()
        self.assertEqual(test_shortener.shorten(1234.5678e6, ""), "1234.5678mn")
        self.assertEqual(test_shortener.shorten(1234e6, ""), "1234.0mn")
        self.assertEqual(test_shortener.shorten(-1234.5678e6, ",.2f"), "-1,234.57mn")

    def test_billion_shortening(self):
        test_shortener = ns.BillionShortening()
        self.assertEqual(test_shortener.shorten(1234.5678e9, ""), "1234.5678bn")
        self.assertEqual(test_shortener.shorten(1234e9, ""), "1234.0bn")
        self.assertEqual(test_shortener.shorten(-1234.5678e9, ",.2f"), "-1,234.57bn")
