from unittest.mock import patch

from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from user.tests.factories.montrek_user_factories import MontrekUserFactory

from baseclasses.dataclasses.montrek_message import (
    MontrekMessageError,
    MontrekMessageInfo,
)
from baseclasses.managers.montrek_manager import MontrekManager
from baseclasses.pages import MontrekPage
from baseclasses.tests.mocks import MockRepository
from baseclasses.views import (
    MontrekCreateUpdateView,
    MontrekDetailView,
    MontrekListView,
    MontrekPageViewMixin,
    MontrekRedirectView,
    MontrekTemplateView,
    MontrekViewMixin,
    navbar,
)
from testing.decorators.add_logged_in_user import add_logged_in_user


class MockRequester:
    def add_mock_request(self, url: str):
        self.request = RequestFactory().get(url)
        self._pass_request_to_middleware()

    def add_mock_request_post(self, url: str, data: dict):
        self.request = RequestFactory().post(url, data)
        self._pass_request_to_middleware()

    def _pass_request_to_middleware(self):
        self.request.user = AnonymousUser()
        session_middleware = SessionMiddleware(lambda request: None)
        session_middleware.process_request(self.request)
        self.request.session.save()
        message_middleware = MessageMiddleware(lambda request: None)
        message_middleware.process_request(self.request)


class MockManager(MontrekTableManager):
    repository_class = MockRepository

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
    repository_class = MockRepository
    document_title = "Guten Tag!"
    footer_text = MockFooter()
    draft = True
    document_name = "whats your name"

    def to_latex(self):
        return "Hallo!"


class MockMontrekView(MontrekViewMixin, MockRequester, MontrekPageViewMixin):
    manager_class = MockManager

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class MockPage(MontrekPage):
    @property
    def tabs(self):
        return []


class MockMontrekTemplateViewNoMethods(MontrekTemplateView, MockRequester):
    page_class = MockPage

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class MockMontrekTemplateView(MockMontrekTemplateViewNoMethods):
    manager_class = MockManager

    def get_template_context(self) -> dict:
        return {}


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


class MockErrors:
    def items(self):
        return [("bla", "blubb")]


class MockFormClass:
    errors = MockErrors()

    def __init__(self, request, repository): ...

    def is_valid(self):
        return False


class MockMontrekCreateView(MontrekCreateUpdateView, MockRequester):
    manager_class = MockManager
    is_hub_based = False
    form_class = MockFormClass
    page_class = MockPage

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)
        self.kwargs = {}


class TestUnderConstruction(TestCase):
    def test_under_construction(self):
        user = MontrekUserFactory()
        self.client.force_login(user)
        response = self.client.get("/under_construction")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "under_construction.html")


class TestMontrekViewMixin(TestCase):
    def test_session_data(self):
        mock_view = MockMontrekListView("/")
        self.assertEqual(
            mock_view.session_data,
            {
                "filter": {},
                "request_path": "/",
                "host_url": "http://testserver",
                "http_referer": None,
                "pages": {},
                "filter_count": {"/": 1},
            },
        )

    def test_session_data_with_query_params(self):
        mock_view = MockMontrekListView("/?param1=value1&param2=value2")
        expected_data = {
            "param1": ["value1"],
            "param2": ["value2"],
            "request_path": "/",
            "host_url": "http://testserver",
            "pages": {},
            "http_referer": None,
            "filter": {},
            "filter_count": {"/": 1},
        }
        self.assertEqual(mock_view.session_data, expected_data)

    def test_session_data_with_multiple_filter_params(self):
        mock_view = MockMontrekListView(
            "/?filter_field=field1&filter_negate=False&filter_lookup=exact&filter_value=value1&filter_field=field2&filter_negate=True&filter_lookup=lgt&filter_value=value2"
        )

        expected_data = {
            "request_path": "/",
            "host_url": "http://testserver",
            "pages": {},
            "http_referer": None,
            "filter": {
                "/": {
                    "field1__exact": {"filter_negate": False, "filter_value": "value1"},
                    "field2__lgt": {"filter_negate": True, "filter_value": "value2"},
                }
            },
            "filter_count": {"/": 1},
        }
        self.assertEqual(mock_view.session_data, expected_data)

    def test_session_data__post(self):
        url = "/"
        mock_view = MockMontrekListView(url)
        data = {"key1": "value1", "key2": "value2"}
        mock_view.add_mock_request_post(url, data)
        for k, v in data.items():
            self.assertEqual(mock_view.session_data[k][0], v)

    def test_session_data_storage(self):
        mock_view = MockMontrekView("/")
        mock_view.request.session["test_key"] = "test_value"
        self.assertEqual(mock_view.session_data["test_key"], "test_value")

    def test_session_data_contains_user_id_for_authenticated_user(self):
        user = MontrekUserFactory()
        mock_view = MockMontrekView("/")
        mock_view.request.user = user
        self.assertEqual(mock_view.session_data["user_id"], user.id)

    def test_session_data_contains_no_user_id_for_anonymous_user(self):
        mock_view = MockMontrekView("/")
        self.assertNotIn("user_id", mock_view.session_data)

    def test_filter_data_handling(self):
        mock_view = MockMontrekListView(
            "/some/path?filter_field=field1&filter_negate=false&filter_lookup=in&filter_value=value1,value2"
        )
        expected_filter_data = {
            "filter": {
                "/some/path": {
                    "field1__in": {
                        "filter_negate": False,
                        "filter_value": ["value1", "value2"],
                    }
                }
            },
        }
        expected_session_data = expected_filter_data.copy()
        expected_session_data["request_path"] = "/some/path"
        expected_session_data["host_url"] = "http://testserver"
        expected_session_data["http_referer"] = None
        expected_session_data["pages"] = {}
        expected_session_data["filter_count"] = {"/some/path": 1}

        self.assertEqual(mock_view.session_data, expected_session_data)
        self.assertEqual(
            mock_view.request.session["filter"], expected_filter_data["filter"]
        )

    def test_repository_object_creation(self):
        mock_view = MockMontrekView("/")
        self.assertIsInstance(mock_view.manager.repository, MockRepository)

    def test_show_repository_messages(self):
        mock_view = MockMontrekView("/")
        mock_view.manager.repository.messages = [
            MontrekMessageError("Error message"),
        ]
        mock_view.manager.messages = [
            MontrekMessageInfo("Info message"),
        ]
        mock_view.show_messages()
        # Retrieve messages from the request
        messages = list(get_messages(mock_view.request))

        # Assert that the messages contain the expected content
        self.assertTrue(
            any(
                msg.message == "Error message" and msg.level_tag == "error"
                for msg in messages
            )
        )
        self.assertTrue(
            any(
                msg.message == "Info message" and msg.level_tag == "info"
                for msg in messages
            )
        )

    def test_get_view_queryset(self):
        mock_view = MockMontrekView("/")
        mock_queryset = mock_view.get_view_queryset()
        self.assertEqual(
            [mqe.field for mqe in mock_queryset], ["item1", "item2", "item3"]
        )

    def test_empty_request_in_date_range_form(self):
        mock_view = MontrekPageViewMixin()
        form_data = mock_view._handle_date_range_form()
        self.assertEqual(form_data, {})


class MockMontrekListView(MontrekListView, MockRequester):
    manager_class = MockManager
    page_class = MockPage
    kwargs = {}

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class MockManagerPdfFails(MontrekTableManager):
    repository_class = MockRepository

    def to_latex(self):
        return "\\textbf{This is a bold text with a missing closing brace."


class MockMontrekListViewPdfFails(MontrekListView, MockRequester):
    manager_class = MockManagerPdfFails
    page_class = MockPage
    kwargs = {}

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class TestMontrekListView(TestCase):
    def test_list_view_base_normal_load(self):
        """
        Test that the page loads normally without the `gen_csv` query parameter.
        """
        test_list_view = MockMontrekListView("dummy")
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)

    def test_list_view_base_csv_generation(self):
        test_list_view = MockMontrekListView("dummy?gen_csv=true")
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertTrue(
            response["Content-Disposition"].startswith('attachment; filename="')
        )

    def test_list_view_base_excel_generation(self):
        test_list_view = MockMontrekListView("dummy?gen_excel=true")
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(
            response["Content-Disposition"].startswith('attachment; filename="')
        )

    def test_list_view_base_pdf_generation(self):
        test_list_view = MockMontrekListView("dummy?gen_pdf=true")
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    @override_settings(IS_TEST_RUN=False)
    def test_list_view_base_pdf_generation__fails(self):
        test_list_view = MockMontrekListViewPdfFails("dummy?gen_pdf=true")
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 302)
        self.assertGreater(len(test_list_view.manager.messages), 0)

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


class TestMontrekDetailView(TestCase):
    def test_gen_pdf(self):
        test_view = MockMontrekDetailViewWrongManager("dummy?gen_pdf=true")
        response = test_view.get(test_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_get_context_data__raise_error(self):
        test_view = MockMontrekDetailViewWrongManager("/")
        test_view.kwargs = {}
        test_view.object = []
        self.assertRaises(ValueError, test_view.get_context_data)


class TestNavbar(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_navbar(self):
        request = self.factory.get("/navbar/")
        response = navbar(request)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")

        # Check Navbar Brand
        brand = soup.find("a", class_="navbar-brand")
        self.assertIsNotNone(brand)
        self.assertEqual(brand.text.strip(), "montrek")

        # Check "Home" link
        home_link = soup.find("a", href="/")
        self.assertIsNotNone(home_link)
        self.assertEqual(home_link.text.strip(), "montrek")

        # Check Dropdown for "Montrek Example"
        dropdown = soup.find("li", class_="dropdown")
        self.assertIsNotNone(dropdown)

        # Verify dropdown title
        dropdown_toggle = dropdown.find("a", class_="dropdown-toggle")
        self.assertIsNotNone(dropdown_toggle)
        self.assertIn("Montrek Example", dropdown_toggle.text)

        # Verify dropdown items
        dropdown_items = dropdown.find_all("li")
        self.assertEqual(len(dropdown_items), 1)  # Should contain one item

        dropdown_link = dropdown_items[0].find("a")
        self.assertIsNotNone(dropdown_link)
        self.assertEqual(dropdown_link.text.strip(), "Montrek Example Report")
        self.assertEqual(dropdown_link["href"], "/montrek_example/")

        # Check individual "Mailing" link (not inside dropdown)
        mailing_link = soup.find("a", href="/mailing/overview")
        self.assertIsNotNone(mailing_link)
        self.assertEqual(mailing_link.text.strip(), "Mailing")


class TestMontrekTemplateView(TestCase):
    def test_no_kwargs(self):
        test_view = MockMontrekTemplateView("/")
        kwargs = {"hallo": "wallo!"}
        test_view.get_context_data(**kwargs)
        self.assertEqual(test_view.kwargs, kwargs)

    def test_no_get_template_context(self):
        test_view = MockMontrekTemplateViewNoMethods("/")
        self.assertRaises(NotImplementedError, test_view.get_context_data)

    def test_get_view_queryset(self):
        test_view = MockMontrekTemplateView("/")
        test_queryset = test_view.get_queryset()
        self.assertEqual(
            [mqe.field for mqe in test_queryset], ["item1", "item2", "item3"]
        )
        self.assertEqual([mqe.value for mqe in test_queryset], [1, 2, 3])


class TestMontrekCreateView(TestCase):
    def test_get_queryset(self):
        test_view = MockMontrekCreateView("/")
        test_queryset = test_view.get_queryset()
        self.assertEqual(
            [mqe.field for mqe in test_queryset], ["item1", "item2", "item3"]
        )
        self.assertEqual([mqe.value for mqe in test_queryset], [1, 2, 3])

    def test_post(self):
        test_view = MockMontrekCreateView("/")
        test_form = test_view.post(test_view.request)
        self.assertEqual(test_form.status_code, 200)


class TestMontrekRedirectView(TestCase):
    def test_no_get_redirect_url(self):
        test_view = MontrekRedirectView()
        self.assertRaises(NotImplementedError, test_view.get_redirect_url)


class ClientLogoViewTest(TestCase):
    @patch("baseclasses.views.config")  # patching the config function
    @add_logged_in_user
    def test_client_logo(self, mock_config):
        # Mock the config value to simulate the environment variable
        mock_config.return_value = "my_logo.png"

        # Make a request to the view
        response = self.client.get(
            reverse("client_logo")
        )  # assuming the view has the URL name 'client_logo'

        # Check that the response is OK (200)
        self.assertEqual(response.status_code, 200)

        # Ensure the context contains the correct logo path
        self.assertIn("client_logo_path", response.context)
        self.assertEqual(response.context["client_logo_path"], "my_logo.png")

        # Check the rendered HTML
        # Check that the static URL for the logo is correct
        self.assertContains(
            response,
            '<img src="/static/logos/my_logo.png" class="img-responsive" alt="Client Logo"/>',
        )

    @patch("baseclasses.views.config")  # patching the config function
    @add_logged_in_user
    def test_client_logo_url(self, mock_config):
        # Mock the config value to simulate the environment variable
        mock_config.return_value = "http://my_logo.png"

        # Make a request to the view
        response = self.client.get(
            reverse("client_logo")
        )  # assuming the view has the URL name 'client_logo'

        # Check that the response is OK (200)
        self.assertEqual(response.status_code, 200)

        # Ensure the context contains the correct logo path
        self.assertIn("client_logo_path", response.context)
        self.assertEqual(response.context["client_logo_path"], "http://my_logo.png")

        # Check the rendered HTML
        # Check that the static URL for the logo is correct
        self.assertContains(
            response,
            '<img src="http://my_logo.png" class="img-responsive" alt="Client Logo"/>',
        )
