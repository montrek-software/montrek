from django.test import TestCase
from reporting.core.reporting_colors import Color, ReportingColors


class TestReportingColors(TestCase):
    def test_lighten_color(self):
        test_cases = [
            # Format: (color_name, hex_code, factor, expected_hex_result)
            ("blue", "#004767", 0.9, "#e5ecef"),
            ("red", "#990000", 0.5, "#cc7f7f"),
            ("green", "#006400", 0.8, "#cce0cc"),
            ("white", "#ffffff", 0.9, "#ffffff"),  # white should stay white
            ("black", "#000000", 0.9, "#e5e5e5"),  # black should go light grey
            ("gray", "#808080", 0.5, "#bfbfbf"),
            ("factor_zero", "#123456", 0.0, "#123456"),  # no lightening
            ("almost_one", "#222222", 0.99, "#fcfcfc"),  # very close to white
            (
                "lowercase_hex",
                "#abcdef",
                0.3,
                "#c4dcf3",
            ),  # ensure lowercase doesn't break
            ("uppercase_hex", "#ABCDEF", 0.3, "#c4dcf3"),  # same as above
        ]

        for name, hex_code, factor, expected in test_cases:
            with self.subTest(name=name, hex_code=hex_code, factor=factor):
                test_color = ReportingColors.lighten_color(
                    Color(name, hex_code), factor
                )
                self.assertEqual(test_color.hex.lower(), expected.lower())

    def test_invalid_factor(self):
        with self.assertRaises(ValueError):
            ReportingColors.lighten_color(Color("invalid", "#123456"), -0.1)
        with self.assertRaises(ValueError):
            ReportingColors.lighten_color(Color("invalid", "#123456"), 1.1)
