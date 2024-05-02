from dataclasses import dataclass


@dataclass
class Color:
    name: str
    hex: str


@dataclass
class ReportingColors:
    WHITE = Color("white", "#FFFFFF")
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

    COLOR_PALETTE = [
        RED,
        BLUE,
        DARK_BLUE,
        LIGHT_BLUE,
        DARK_GREEN,
        DARK_ORANGE,
        YELLOW,
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
