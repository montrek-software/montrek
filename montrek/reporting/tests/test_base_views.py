"""The base list and details views together with the table and details
managers of this app and the download registry of the info app."""

from baseclasses.dataclasses.montrek_message import MontrekMessageWarning
from baseclasses.managers.montrek_manager import MontrekManager
from baseclasses.tests.mocks import MockPage, MockRepository, MockRequester
from baseclasses.views import MontrekDetailView, MontrekListView
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from info.repositories.download_registry_repositories import DownloadRegistryRepository
from testing.decorators.add_logged_in_user import add_logged_in_user

from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager


class MockManager(MontrekTableManager):
    repository_class = MockRepository  # type: ignore[assignment]  # test double, not a MontrekRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(attr="field", name="Field"),
            te.IntTableElement(attr="value", name="Value"),
            te.LinkTableElement(
                name="Link",
                url="home",
                kwargs={},
                hover_text="Link",
                icon="icon",
            ),
        ]


class MockFooter:
    def to_latex(self):
        return "Guten Abend"


class MockManager2(MontrekManager):
    repository_class = MockRepository  # type: ignore[assignment]  # test double, not a MontrekRepository
    document_title = "Guten Tag!"
    footer_text = MockFooter()
    draft = True
    document_name = "whats your name"

    def to_latex(self):
        return "Hallo!"

    def to_pdf_html(self) -> str:
        return "<p>Test PDF content</p>"


class MockMontrekListViewWrongManager(MontrekListView, MockRequester):
    manager_class = MockManager2
    page_class = MockPage

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class MockMontrekDetailViewWrongManager(MontrekDetailView, MockRequester):
    manager_class = MockManager2
    is_hub_based = False

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class MockMontrekListView(MontrekListView, MockRequester):
    manager_class = MockManager
    page_class = MockPage
    kwargs = {}

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class MockManagerMessageWhileRendering(MockManager):
    def to_html(self):
        html = super().to_html()
        self.add_message(MontrekMessageWarning("Added while rendering"))
        return html


class MockMontrekListViewMessageWhileRendering(MockMontrekListView):
    manager_class = MockManagerMessageWhileRendering


class MockManagerPdfFails(MontrekTableManager):
    repository_class = MockRepository  # type: ignore[assignment]  # test double, not a MontrekRepository

    def to_latex(self):
        return "\\textbf{This is a bold text with a missing closing brace."

    def to_pdf_html(self) -> str:
        raise RuntimeError("WeasyPrint PDF generation intentionally broken")


class MockMontrekListViewPdfFails(MontrekListView, MockRequester):
    manager_class = MockManagerPdfFails
    page_class = MockPage
    kwargs = {}

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class TestMontrekListView(TestCase):
    def test_list_view_shows_messages_added_while_rendering(self):
        test_list_view = MockMontrekListViewMessageWhileRendering("dummy")

        test_list_view.get(test_list_view.request)

        messages = [message.message for message in get_messages(test_list_view.request)]
        self.assertEqual(messages, ["Added while rendering"])

    def test_list_view_base_normal_load(self):
        """
        Test that the page loads normally without the `gen_csv` query parameter.
        """
        test_list_view = MockMontrekListView("dummy")
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)

    @add_logged_in_user()
    def test_list_view_base_csv_generation(self):
        test_list_view = MockMontrekListView("dummy?gen_csv=true")
        test_list_view.kwargs = {"user_id": self.user.id}
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertTrue(
            response["Content-Disposition"].startswith('attachment; filename="')
        )
        repo = DownloadRegistryRepository()
        self.assertEqual(repo.receive().count(), 1)

    @add_logged_in_user()
    def test_list_view_base_excel_generation(self):
        test_list_view = MockMontrekListView("dummy?gen_excel=true")
        test_list_view.kwargs = {"user_id": self.user.id}
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(
            response["Content-Disposition"].startswith('attachment; filename="')
        )
        repo = DownloadRegistryRepository()
        self.assertEqual(repo.receive().count(), 1)

    @add_logged_in_user()
    def test_list_view_base_markdown_generation(self):
        test_list_view = MockMontrekListView("dummy?gen_md=true")
        test_list_view.kwargs = {"user_id": self.user.id}
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/markdown")
        self.assertTrue(
            response["Content-Disposition"].startswith('attachment; filename="')
        )
        self.assertTrue(response["Content-Disposition"].endswith('.md"'))
        repo = DownloadRegistryRepository()
        self.assertEqual(repo.receive().count(), 1)

    @add_logged_in_user()
    def test_list_view_base_pdf_generation(self):
        test_list_view = MockMontrekListView("dummy?gen_pdf=true")
        test_list_view.kwargs = {"user_id": self.user.id}

        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        repo = DownloadRegistryRepository()
        self.assertEqual(repo.receive().count(), 1)

    @override_settings(IS_TEST_RUN=False)
    @add_logged_in_user()
    def test_list_view_base_pdf_generation__fails(self):
        test_list_view = MockMontrekListViewPdfFails("dummy?gen_pdf=true")
        test_list_view.kwargs = {"user_id": self.user.id}
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 302)
        self.assertGreater(len(test_list_view.manager.messages), 0)
        repo = DownloadRegistryRepository()
        self.assertEqual(repo.receive().count(), 0)

    def test_list_view_base_filter_reset(self):
        mock_view = MockMontrekListView(
            "/dummy?filter_field=field1&filter_negate=false&filter_lookup=in&filter_value=value1,value2"
        )
        response = mock_view.get(mock_view.request)
        self.assertNotEqual(mock_view.request.session["filter"]["/dummy"], {})
        test_list_view = MockMontrekListView("dummy?action=reset")
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(test_list_view.request.session["filter"]["/dummy"], {})

    def test_list_view_base_filter_add(self):
        test_list_view = MockMontrekListView("dummy?action=add_filter")
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(test_list_view.request.session["filter_count"]["/dummy"], 2)

    def test_get_context_data__raise_error(self):
        test_view = MockMontrekListViewWrongManager("/")
        test_view.kwargs = {}
        self.assertRaises(ValueError, test_view.get_context_data, **{"object_list": []})

    def test_list_view_base__add_paginate_by(self):
        test_list_view = MockMontrekListView("dummy?action=add_paginate_by")
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(test_list_view.request.session["paginate_by"]["/dummy"], 15)

    def test_list_view_base__sub_paginate_by(self):
        test_list_view = MockMontrekListView("dummy?action=sub_paginate_by")
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(test_list_view.request.session["paginate_by"]["/dummy"], 5)

    def test_list_view_base__set_is_compact_format__true(self):
        test_list_view = MockMontrekListView("dummy?action=is_compact_format_true")
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            test_list_view.request.session["is_compact_format"]["/dummy"], True
        )

    def test_list_view_base__set_is_compact_format__false(self):
        test_list_view = MockMontrekListView("dummy?action=is_compact_format_false")
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            test_list_view.request.session["is_compact_format"]["/dummy"], False
        )

    def test_list_view_base__order_field(self):
        test_list_view = MockMontrekListView("dummy?order_action=field_a&page=2")
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            test_list_view.request.session["order_fields"]["/dummy"], ["field_a"]
        )
        self.assertEqual(test_list_view.request.session["pages"]["/dummy"], ["1"])
        request = test_list_view.request
        test_list_view = MockMontrekListView("dummy?order_action=field_b")
        test_list_view.request.session["order_fields"] = request.session["order_fields"]
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            test_list_view.request.session["order_fields"]["/dummy"], ["field_b"]
        )
        request = test_list_view.request
        test_list_view = MockMontrekListView("dummy?order_action=field_b")
        test_list_view.request.session["order_fields"] = request.session["order_fields"]
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            test_list_view.request.session["order_fields"]["/dummy"], ["-field_b"]
        )
        request = test_list_view.request
        test_list_view = MockMontrekListView("dummy?order_action=field_b")
        test_list_view.request.session["order_fields"] = request.session["order_fields"]
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            test_list_view.request.session["order_fields"]["/dummy"], [None]
        )
        request = test_list_view.request
        test_list_view = MockMontrekListView("dummy?order_action=field_b")
        test_list_view.request.session["order_fields"] = request.session["order_fields"]
        response = test_list_view.get(test_list_view.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            test_list_view.request.session["order_fields"]["/dummy"], ["field_b"]
        )


class TestMontrekDetailView(TestCase):
    @add_logged_in_user()
    def test_gen_pdf(self):
        test_view = MockMontrekDetailViewWrongManager("dummy?gen_pdf=true")
        test_view.kwargs = {"user_id": self.user.id}
        response = test_view.get(test_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        repo = DownloadRegistryRepository()
        self.assertEqual(repo.receive().count(), 1)

    def test_get_context_data__raise_error(self):
        test_view = MockMontrekDetailViewWrongManager("/")
        test_view.kwargs = {}
        test_view.object = []
        self.assertRaises(ValueError, test_view.get_context_data)
