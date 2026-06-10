from django.conf import settings
from django.test import TestCase

from reporting.core import gold_plotly_theme
from reporting.core.reporting_colors import Color, ReportingColors

# Note: title_color() and gold_color_palette() are @cache-d, so they read
# PRIMARY_COLOR / SECONDARY_COLOR once per process. Tests therefore build
# their expectations from the real settings instead of override_settings.


class TestMixColors(TestCase):
    def test_full_weight_returns_first_color(self):
        mixed = gold_plotly_theme.mix_colors(
            ReportingColors.RED, ReportingColors.WHITE, 1.0
        )
        self.assertEqual(mixed.hex.lower(), ReportingColors.RED.hex.lower())

    def test_zero_weight_returns_second_color(self):
        mixed = gold_plotly_theme.mix_colors(
            ReportingColors.RED, ReportingColors.WHITE, 0.0
        )
        self.assertEqual(mixed.hex.lower(), ReportingColors.WHITE.hex.lower())

    def test_midpoint_blend(self):
        mixed = gold_plotly_theme.mix_colors(
            ReportingColors.BLACK, ReportingColors.WHITE, 0.5
        )
        self.assertEqual(mixed.hex, "#808080")

    def test_mixed_color_name_combines_inputs(self):
        mixed = gold_plotly_theme.mix_colors(
            Color("one", "#000000"), Color("two", "#ffffff"), 0.5
        )
        self.assertEqual(mixed.name, "one_two_mix")

    def test_invalid_weight_raises(self):
        for weight in (-0.1, 1.1):
            with self.assertRaises(ValueError):
                gold_plotly_theme.mix_colors(
                    ReportingColors.BLACK, ReportingColors.WHITE, weight
                )


class TestTitleColor(TestCase):
    def test_matches_h2_blend_of_primary_into_text(self):
        expected = gold_plotly_theme.mix_colors(
            Color("primary", settings.PRIMARY_COLOR),
            gold_plotly_theme.TEXT,
            0.65,
        ).hex
        self.assertEqual(gold_plotly_theme.title_color(), expected)


class TestGoldColorPalette(TestCase):
    def test_brand_colors_come_first(self):
        palette = gold_plotly_theme.gold_color_palette()
        self.assertEqual(palette[0], settings.PRIMARY_COLOR)
        self.assertEqual(palette[1], settings.SECONDARY_COLOR)

    def test_brand_colors_not_duplicated_in_fallbacks(self):
        palette = gold_plotly_theme.gold_color_palette()
        branded = {settings.PRIMARY_COLOR.lower(), settings.SECONDARY_COLOR.lower()}
        fallbacks = {color.lower() for color in palette[2:]}
        self.assertFalse(branded & fallbacks)

    def test_fallbacks_preserve_reporting_palette_order(self):
        palette = gold_plotly_theme.gold_color_palette()
        branded = {settings.PRIMARY_COLOR.lower(), settings.SECONDARY_COLOR.lower()}
        expected = [
            color.hex
            for color in ReportingColors.COLOR_PALETTE
            if color.hex.lower() not in branded
        ]
        self.assertEqual(palette[2:], expected)


class TestGoldLayout(TestCase):
    def test_layout_carries_title_and_gold_tokens(self):
        layout = gold_plotly_theme.gold_layout("My Report")
        self.assertEqual(layout["title_text"], "My Report")
        self.assertEqual(layout["title_font_color"], gold_plotly_theme.title_color())
        self.assertIn("Inter", layout["font"]["family"])
        self.assertEqual(layout["font"]["color"], gold_plotly_theme.TEXT_MUTED.hex)
        self.assertEqual(layout["modebar"]["activecolor"], settings.PRIMARY_COLOR)

    def test_axis_uses_hairline_grid(self):
        axis = gold_plotly_theme.gold_axis()
        self.assertEqual(axis["gridcolor"], gold_plotly_theme.BORDER.hex)
        self.assertEqual(axis["color"], gold_plotly_theme.TEXT_MUTED.hex)
