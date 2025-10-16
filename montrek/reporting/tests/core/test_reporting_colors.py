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

    def test_get_contrast_font_color(self):
        test_cases = [
            # Format: (color_name, hex_code, expected_font_color)
            ("blue", "#004767", "white"),
            ("red", "#990000", "white"),
            ("green", "#006400", "white"),
            ("white", "#ffffff", "black"),  # white should stay white
            ("black", "#000000", "white"),  # black should go light grey
            ("gray", "#808080", "white"),
            ("factor_zero", "#123456", "white"),  # no lightening
            ("almost_one", "#222222", "white"),  # very close to white
            ("uppercase_hex", "#ABCDEF", "black"),  # same as above
        ]

        for name, hex_code, expected in test_cases:
            with self.subTest(name=name, hex_code=hex_code):
                test_color = Color(name, hex_code)
                font_contrast_color = ReportingColors.contrast_font_color(test_color)
                self.assertEqual(font_contrast_color.name, expected)


class TestColors(TestCase):
    def test_color_to_rgb(self):
        test_cases = [
            # Format: (color_name, hex_code, factor, expected_hex_result)
            ("blue", "#004767", [0, 71, 103]),
            ("red", "#990000", [153, 0, 0]),
            ("green", "#006400", [0, 100, 0]),
            ("white", "#ffffff", [255, 255, 255]),  # white should stay white
            ("black", "#000000", [0, 0, 0]),  # black should go light grey
            ("gray", "#808080", [128, 128, 128]),
            ("factor_zero", "#123456", [18, 52, 86]),  # no lightening
            ("almost_one", "#222222", [34, 34, 34]),  # very close to white
            ("uppercase_hex", "#ABCDEF", [171, 205, 239]),  # same as above
        ]

        for name, hex_code, expected in test_cases:
            with self.subTest(name=name, hex_code=hex_code):
                test_color = Color(name, hex_code)
                self.assertEqual(test_color.rgb(), expected)

    def test_color_brightness(self):
        test_cases = [
            # Format: (color_name, hex_code, factor, expected_hex_result)
            ("blue", "#004767", 68.555),
            ("red", "#990000", 45.747),
            ("green", "#006400", 11.4),
            ("white", "#ffffff", 255.0),  # white should stay white
            ("black", "#000000", 0.0),  # black should go light grey
            ("gray", "#808080", 128.0),
            ("factor_zero", "#123456", 61.792),  # no lightening
            ("almost_one", "#222222", 34.0),  # very close to white
            ("uppercase_hex", "#ABCDEF", 214.792),  # same as above
        ]

        for name, hex_code, expected in test_cases:
            with self.subTest(name=name, hex_code=hex_code):
                test_color = Color(name, hex_code)
                self.assertEqual(test_color.brightness(), expected)
