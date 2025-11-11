from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class DocsPageABC(MontrekPage):
    def get_tabs(self) -> list | tuple[TabElement]:
        return []
