from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage
from django.urls import reverse
from docs_framework.mixins.docs_mixins import DocsFilesMixin


class DocsPageABC(MontrekPage, DocsFilesMixin):
    docs_url: str = "not_set"

    def get_tabs(self) -> list | tuple[TabElement]:
        docs_files = self.get_docs_files()
        tabs = []
        for docs_file in docs_files:
            tabs.append(
                TabElement(
                    name=docs_file.docs_name,
                    link=reverse(
                        self.docs_url, kwargs={"docs_name": docs_file.docs_name}
                    ),
                    html_id=f"tab_docs_{docs_file.docs_name}",
                )
            )
        return tabs
