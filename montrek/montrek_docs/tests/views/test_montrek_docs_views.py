from montrek_docs.views.montrek_docs_views import MontrekDocsView
from testing.test_cases.view_test_cases import MontrekReportViewTestCase


class TestMontrekDocsViews(MontrekReportViewTestCase):
    view_class = MontrekDocsView
    viewname = "montrek_docs"
    expected_number_of_report_elements = 1

    def url_kwargs(self) -> dict:
        return {"docs_name": "montrek_views_and_subclasses"}
