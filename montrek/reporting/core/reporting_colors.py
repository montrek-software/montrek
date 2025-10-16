from dataclasses import dataclass


@dataclass
class Color:
    name: str
    hex: str

    def rgb(self) -> list[int]:
        hex_color = self.hex.lstrip("#")
        return [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]

    def brightness(self) -> float:
        r, g, b = self.rgb()
        return (299 * r + 587 * g + 114 * b) / 1000


@dataclass
class ReportingColors:
    WHITE = Color("white", "#FFFFFF")
    BLACK = Color("black", "#000000")
    BLUE = Color("blue", "#004767")
    LIGHT_BLUE = Color("lightblue", "#E6F2F8")
    DARK_BLUE = Color("darkblue", "#002F6C")
    RED = Color("red", "#BE0D3E")
    DARKER_RED = Color("darkerred", "#821621")
    MEDIUM_BLUE = Color("mediumblue", "#2B6D8B")
    SOFT_ROSE = Color("softrose", "#D3A9A1")
    SOFT_SKY = Color("softsky", "#6B93B0")
    LIGHT_ROSE = Color("lightrose", "#FBE8E8")
    LIGHT_SKY = Color("lightsky", "#B1CFE2")
    BRIGHTER_RED = Color("brighterred", "#E64C4C")
    DARK_GREEN = Color("darkgreen", "#1B5E20")
    DARK_ORANGE = Color("darkorange", "#FF6F00")
    YELLOW = Color("yellow", "#FDD835")
    BROWN = Color("brown", "#6D4C41")
    PURPLE = Color("purple", "#7E57C2")
    TEAL = Color("teal", "#26A69A")
    BRIGHTER_RED = Color("brighterred", "#D32F2F")
    BRIGHTER_BLUE = Color("brighterblue", "#0277BD")
    BRIGHTER_GREEN = Color("brightergreen", "#388E3C")
    BRIGHTER_ORANGE = Color("brighterorange", "#FFA000")
    BRIGHTER_YELLOW = Color("brighteryellow", "#FBC02D")
    DARKER_BROWN = Color("darkerbrown", "#5D4037")
    LIGHT_GREY = Color("lightgrey", "#F4F4F4")
    GREY = Color("grey", "#BDBDBD")

    COLOR_PALETTE_SKIM = [
        RED,
        BLUE,
        DARK_GREEN,
        DARK_ORANGE,
        DARK_BLUE,
        YELLOW,
        LIGHT_ROSE,
        LIGHT_BLUE,
        BROWN,
        PURPLE,
        TEAL,
        BRIGHTER_RED,
        BRIGHTER_BLUE,
        BRIGHTER_GREEN,
        BRIGHTER_ORANGE,
        BRIGHTER_YELLOW,
        DARKER_BROWN,
        LIGHT_GREY,
        GREY,
    ]

    COLOR_PALETTE = COLOR_PALETTE_SKIM + [DARK_BLUE] * 100

    COLOR_PALETTE_GRADIENT = [
        RED,
        BLUE,
        LIGHT_BLUE,
        DARKER_RED,
        MEDIUM_BLUE,
        SOFT_ROSE,
        SOFT_SKY,
        LIGHT_ROSE,
        LIGHT_SKY,
        BRIGHTER_RED,
    ]

    def hex_color_palette(self):
        return [color.hex for color in self.COLOR_PALETTE]

    @classmethod
    def lighten_color(cls, color: Color, factor=0.9) -> Color:
        """
        Lighten the given hex color by a factor (0 < factor < 1).
        `factor` is how much closer to white the color should move.
        """
        if factor < 0.0 or factor > 1.0:
            raise ValueError("factor needs to be between 0 and 1")
        r, g, b = color.rgb()

        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)

        return Color(f"{color.name}_light", "#{:02x}{:02x}{:02x}".format(r, g, b))

    @classmethod
    def contrast_font_color(cls, color: Color) -> Color:
        return cls.BLACK if color.brightness() > 128 else cls.WHITE
