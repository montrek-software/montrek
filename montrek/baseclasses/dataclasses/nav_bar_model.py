from dataclasses import dataclass, field


@dataclass
class NavBarModel:
    """Model for the navigation bar"""

    app_name: str

    @property
    def display_name(self) -> str:
        """Display name for the app"""
        return self.app_name.replace("_", " ").title()


@dataclass
class NavBarDropdownModel:
    """Model for the navigation bar dropdown"""

    dropdown_name: str
    dropdown_items: list[NavBarModel] = field(default_factory=list)
    force_display_name: str | None = None

    @property
    def display_name(self) -> str:
        """Display name for the dropdown"""
        if self.force_display_name:
            return self.force_display_name
        return self.dropdown_name.replace("mt_", "").replace("_", " ").title()
