"""Plotly chart theming matched to the gold theme design tokens.

Mirrors the --mt-* CSS custom properties defined in
baseclasses/templates/partials/gold_theme.html so that charts and the
surrounding UI share one visual language. Client branding flows in via
settings.PRIMARY_COLOR / settings.SECONDARY_COLOR, exactly as in the CSS.
"""

from functools import cache

from django.conf import settings

from reporting.core.reporting_colors import Color, ReportingColors

# Mirrors the neutral --mt-* tokens in gold_theme.html
TEXT = Color("text", "#1d2430")
TEXT_MUTED = Color("text_muted", "#5b6573")
BORDER = Color("border", "#e5e8ec")
BORDER_STRONG = Color("border_strong", "#d2d7dd")
SURFACE = ReportingColors.WHITE

# Inter with fallbacks; static exports (kaleido) fall back to Arial.
FONT_FAMILY = '"Inter Variable", "Inter", system-ui, "Segoe UI", Arial, sans-serif'


def mix_colors(color: Color, other: Color, weight: float) -> Color:
    """Blend `color` into `other`, mirroring CSS color-mix(in srgb, ...)."""
    if not 0.0 <= weight <= 1.0:
        raise ValueError("weight needs to be between 0 and 1")
    mixed = [
        round(c * weight + o * (1 - weight))
        for c, o in zip(color.rgb(), other.rgb(), strict=True)
    ]
    return Color(f"{color.name}_{other.name}_mix", "#{:02x}{:02x}{:02x}".format(*mixed))


@cache
def _primary_color() -> Color:
    return Color("primary", settings.PRIMARY_COLOR)


@cache
def _secondary_color() -> Color:
    return Color("secondary", settings.SECONDARY_COLOR)


@cache
def title_color() -> str:
    """Chart title color; matches h2 in gold_theme.html (accent 65% / text)."""
    return mix_colors(_primary_color(), TEXT, 0.65).hex


def gold_layout(title: str | None = None) -> dict:
    """Base figure layout shared by all reporting plots."""
    return {
        "title_text": title,
        "title_font_color": title_color(),
        "font": {
            "family": FONT_FAMILY,
            "size": 13,
            "color": TEXT_MUTED.hex,
        },
        "paper_bgcolor": SURFACE.hex,
        "plot_bgcolor": SURFACE.hex,
        "margin": {"l": 0, "r": 0},
        "legend": {"font": {"color": TEXT_MUTED.hex}},
    }


def gold_axis() -> dict:
    """Axis styling: muted labels, hairline grid (mirrors table dividers)."""
    return {
        "color": TEXT_MUTED.hex,
        "gridcolor": BORDER.hex,
        "zerolinecolor": BORDER_STRONG.hex,
    }


@cache
def gold_color_palette() -> list[str]:
    """Trace colors: client brand colors first, then distinguishable fallbacks."""
    branded = [_primary_color().hex, _secondary_color().hex]
    branded_lower = {color.lower() for color in branded}
    fallbacks = [
        color.hex
        for color in ReportingColors.COLOR_PALETTE
        if color.hex.lower() not in branded_lower
    ]
    return branded + fallbacks
