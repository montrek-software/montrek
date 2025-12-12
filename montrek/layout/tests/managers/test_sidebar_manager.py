import os

from baseclasses.tests.mocks import MockRepository
from django.test import TestCase
from django.urls import reverse
from layout.managers.sidebar_manager import SidebarLinkTableElement, SidebarManagerABC

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def get_test_file_path(file_name):
    return os.path.join(TEST_DATA_DIR, file_name)


class MockSidebarLinkTableElement(SidebarLinkTableElement): ...


class MockSidebarManager(SidebarManagerABC):
    repository_class = MockRepository
    group_field = "field"

    def link(self) -> SidebarLinkTableElement:
        return MockSidebarLinkTableElement(
            name="Test Link",
            url="home",
            kwargs={},
            text="report_section_list_name",
            hover_text="View Expert Evaluation",
        )


class MockSidebarManagerExpanded(MockSidebarManager):
    def compare_url(self):
        return reverse("home", kwargs={})

    def link(self) -> SidebarLinkTableElement:
        return MockSidebarLinkTableElement(
            name="Test Link",
            url="home",
            kwargs={},
            text="report_section_list_name",
            hover_text="View Expert Evaluation",
            compare_url=self.compare_url(),
        )


class TestSidebarManager(TestCase):
    rebase = True

    def test_link_not_implemented(self):
        manager = SidebarManagerABC()
        self.assertRaises(NotImplementedError, manager.link)

    def test_sidebar_html(self):
        manager = MockSidebarManager()
        test_html = manager.to_html()
        exp_content_fp = get_test_file_path("test_sidebar_html.txt")
        if self.rebase:
            with open(exp_content_fp, "w") as f:
                f.write(test_html)
        with open(exp_content_fp) as f:
            exp_content = f.read()
        self.assertEqual(
            test_html.replace(" ", "").replace("\n", ""),
            exp_content.replace(" ", "").replace("\n", ""),
        )

    def test_sidebar_html_expanded(self):
        manager = MockSidebarManagerExpanded()
        test_html = manager.to_html()
        exp_content_fp = get_test_file_path("test_sidebar_html_expanded.txt")
        if self.rebase:
            with open(exp_content_fp, "w") as f:
                f.write(test_html)
        with open(exp_content_fp) as f:
            exp_content = f.read()
        self.assertEqual(
            test_html.replace(" ", "").replace("\n", ""),
            exp_content.replace(" ", "").replace("\n", ""),
        )
