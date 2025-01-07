from django.test import TestCase
from baseclasses.pages import MontrekDetailsPage, MontrekPage, NoPage
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.tests.mocks import MockRepository


class MockMontrekPage(MontrekPage):
    page_title = "Mock Montrek Page"

    def get_tabs(self):
        return (
            TabElement(
                name="TestName",
                link="TestLink",
                html_id="id_test",
            ),
        )


class MockMontrekDetailsPage(MontrekDetailsPage):
    repository_class = MockRepository
    title_field = "field"


class TestMontrekPage(TestCase):
    def test_montrek_page_not_implemented(self):
        page = MontrekPage()
        with self.assertRaises(NotImplementedError):
            page.tabs()

    def test_montrek_page_get_tabs(self):
        page = MockMontrekPage()
        self.assertEqual(page.page_title, "Mock Montrek Page")
        page.set_active_tab("id_test")
        self.assertEqual(page.tabs[0].active, "active")

        page.set_active_tab("")
        self.assertEqual(page.tabs[0].active, "")

    def test_no_page(self):
        page = NoPage()
        with self.assertRaises(NotImplementedError):
            page.get_tabs()


class TestMontrekDetailsPage(TestCase):
    def test_montrek_details_page(self):
        page = MockMontrekDetailsPage(pk=0)
        self.assertEqual(page.page_title, "item1")

    def test_montrek_details_page_no_pk(self):
        with self.assertRaises(ValueError) as e:
            MockMontrekDetailsPage()
        self.assertEqual(
            str(e.exception), "MockMontrekDetailsPage needs pk specified in url!"
        )
