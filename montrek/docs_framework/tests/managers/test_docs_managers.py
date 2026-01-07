from bs4 import BeautifulSoup
from django.test import TestCase

from docs_framework.managers.docs_managers import DocsManager
from docs_framework.mixins.docs_mixins import DocsFilesMixin


class TestDocsManager(TestCase, DocsFilesMixin):
    def setUp(self):
        docs_file = self.get_docs_file_by_name("docs_1")
        self.manager = DocsManager({"docs_file_path": docs_file.docs_path})

    def test_convert_md_to_html(self):
        html = self.manager.to_html()[0]
        soup = BeautifulSoup(html, "html.parser")

        # Headers
        h1 = soup.find("h1")
        self.assertIsNotNone(h1)
        self.assertEqual(h1.get_text(strip=True), "This is a Header")

        h2 = soup.find("h2")
        self.assertIsNotNone(h2)
        self.assertEqual(h2.get_text(strip=True), "And a Subheader")

        # Paragraph
        p = soup.find("p")
        self.assertIsNotNone(p)
        self.assertEqual(p.get_text(strip=True), "And some text")

        # Table
        table = soup.find("table")
        self.assertIsNotNone(table)

        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        self.assertEqual(headers, ["Maybe a", "little"])

        rows = table.find("tbody").find_all("tr")
        self.assertEqual(
            [[td.get_text(strip=True) for td in row.find_all("td")] for row in rows],
            [
                ["or", "so..."],
                ["and", "on"],
            ],
        )
