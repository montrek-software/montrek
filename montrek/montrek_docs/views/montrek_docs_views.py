from docs_framework.views.docs_views import DocsViewABC
from montrek_docs.pages.montrek_docs_pages import MontrekDocsPage


class MontrekDocsView(DocsViewABC):
    page_class = MontrekDocsPage
