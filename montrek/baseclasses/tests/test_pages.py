from django.test import TestCase
from baseclasses.pages import MontrekPage, NoPage
from baseclasses.dataclasses.view_classes import TabElement


class MockMontrekPage(MontrekPage):
    page_title = "Mock Montrek Page"

    def get_tabs(self):
        return (
            TabElement(
                name="TestName",
                link="TestLink",
                html_id="id_test",
                actions=(),
            ),
        )


class TestMontrekPage(TestCase):
    def test_montrek_page_not_implemented(self):
        page = MontrekPage()
        with self.assertRaises(NotImplementedError):
            page.tabs()

    def test_montrek_page_get_tabs(self):
        page = MockMontrekPage()
        self.assertEqual(page.page_title, "Mock Montrek Page")
        page.set_active_tab("id_test")
        self.assertEqual(page.tabs[0].active , "active")

        page.set_active_tab("")
        self.assertEqual(page.tabs[0].active , "")

    def test_no_page(self):
        page = NoPage()
        with self.assertRaises(NotImplementedError):
            page.get_tabs()

