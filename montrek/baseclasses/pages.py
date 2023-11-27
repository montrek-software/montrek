class MontrekPage:
    @property
    def tabs(self):
        raise NotImplementedError("MontrekPage needs tabs!")

    def set_active_tab(self, active_tab: str):
        for tab in self.tabs:
            if tab.html_id == active_tab:
                tab.active = "active"
            else:
                tab.active = ""
