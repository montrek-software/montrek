from baseclasses.repositories.montrek_repository import MontrekRepository


class MontrekPage:
    page_title = "page_title not set!"
    show_date_range_selector = False

    def __init__(self, **kwargs):
        self._tabs = None

    def get_tabs(self):
        raise NotImplementedError("MontrekPage needs get_tabs method!")

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


class MontrekDetailsPage(MontrekPage):
    repository_class: type[MontrekRepository]
    title_field: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._raise_for_missing_pk(**kwargs)
        self._set_page_title(pk=kwargs["pk"])

    def _raise_for_missing_pk(self, **kwargs):
        if "pk" not in kwargs:
            raise ValueError(f"{self.__class__.__name__} needs pk specified in url!")

    def _set_page_title(self, pk):
        repository = self.repository_class({})
        self.obj = repository.receive().get(pk=pk)
        self.page_title = getattr(self.obj, self.title_field)


class NoPage(MontrekPage):
    def get_tabs(self):
        raise NotImplementedError("MontrekView needs a Page!")
