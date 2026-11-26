"""The navigation of the base templates, filled from the apps of this
project that the tests below put into NAVBAR_APPS."""

from bs4 import BeautifulSoup
from django.test import TestCase, override_settings
from django.urls import reverse
from testing.decorators.add_logged_in_user import add_logged_in_user

navigation_settings = override_settings(
    NAVBAR_APPS=["mailing", "info", "montrek_example.montrek_example_report", ""],
    NAVBAR_RENAME={"info": "Amazing App"},
)


@navigation_settings
class TestHomePage(TestCase):
    @add_logged_in_user
    def test_home_page_shows_launchpad(self):
        response = self.client.get(reverse("home"))
        soup = BeautifulSoup(response.content, "html.parser")

        cards = soup.find_all("a", class_="launchpad-card")
        card_hrefs = [card["href"] for card in cards]
        self.assertIn("/montrek_example/", card_hrefs)
        self.assertIn("/mailing/overview", card_hrefs)

    @add_logged_in_user
    @override_settings(PROJECT_NAME="mt_test_project")
    def test_browser_title_prefixes_page_title(self):
        response = self.client.get("/montrek_example/")
        soup = BeautifulSoup(response.content, "html.parser")
        title = soup.title.text.strip()
        self.assertTrue(title.endswith("– Test Project"), msg=title)
        self.assertGreater(len(title), len("– Test Project"))


@navigation_settings
class TestNavbar(TestCase):
    @add_logged_in_user
    @override_settings(DEBUG=False)
    def test_navbar(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")

        # Check "Home" link
        home_link = soup.find("a", href="/home")
        self.assertIsNotNone(home_link)
        self.assertEqual(home_link.text.strip(), "Home")

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

        # Check individual "Info" link (renamed)
        mailing_link = soup.find("a", href="/info/info")
        self.assertIsNotNone(mailing_link)
        self.assertEqual(mailing_link.text.strip(), "Amazing App")
