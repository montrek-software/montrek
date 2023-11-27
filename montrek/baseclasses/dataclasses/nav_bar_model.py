from dataclasses import dataclass

@dataclass
class NavBarModel:
    """Model for the navigation bar"""
    app_name: str

    @property
    def display_name(self) -> str:
        """Display name for the app"""
        return self.app_name.replace("_", " ").title()
