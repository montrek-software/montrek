class MontrekPage:
    page_title = "page_title not set!"
    show_date_range_selector = False
    def __init__(self, **kwargs):
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


class NoPage(MontrekPage):
    def get_tabs(self):
        raise NotImplementedError("MontrekView needs a Page!")
