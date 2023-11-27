class MontrekPage:
    page_title = "page_title not set!"
    def __init__(self):
        self._tabs = None


    def get_tabs(self):
        raise NotImplementedError("MontrekPage needs tabs!")

    @property
    def tabs(self):
        if self._tabs is None:
            self._tabs = self.get_tabs()
        return self._tabs

    def set_active_tab(self, active_tab: str):
        for tab in self.tabs:
            if tab.html_id == active_tab:
                tab.active = "active"
            else:
                tab.active = ""


class NoAppPage(MontrekPage):
    def get_tabs(self):
        raise NotImplementedError("MontrekView needs a Page!")

class NoPage(MontrekPage):
    def __init__(self, hub_entity_id:int):
        super.__init__(self)
        raise NotImplementedError("MontrekView needs a Page!")
