"""How many round trips a report page costs.

A report defers its body to HTMX so the shell paints immediately. The skeleton
shown while the body is built is static, so fetching it is a request that
returns nothing the shell could not have rendered itself - and it used to cost
one: page, skeleton, report. The shell now renders the skeleton inline, already
asking for ``state=loading``, which leaves page and report.

Nothing about the rendered result changes, so only the request sequence catches
a regression here.
"""

from django.test import TestCase
from django.urls import reverse

from testing.decorators import add_logged_in_user

LOADING_STATE_VALS = '{"state":"loading"}'
REPORT_CONTENT_ID = 'id="report-content"'


class ReportLoadingTestCase(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.url = reverse("montrek_example_report")

    def full_page(self):
        return self.client.get(self.url)

    def htmx_get(self, **query):
        return self.client.get(self.url, query, headers={"hx-request": "true"})


class TestTheShellAsksForTheReportDirectly(ReportLoadingTestCase):
    def test_the_shell_carries_the_loading_state(self):
        """Without this the shell's first HTMX call only fetches the skeleton,
        and the report needs a third request."""
        content = self.full_page().content.decode()

        self.assertIn(LOADING_STATE_VALS, content)

    def test_the_shell_renders_the_skeleton_itself(self):
        response = self.full_page()

        self.assertTemplateUsed(response, "partials/montrek_report_loading.html")
        self.assertIn("loader-container", response.content.decode())

    def test_the_shell_defines_the_htmx_target_exactly_once(self):
        """Only the shell is checked here - the old nesting (the skeleton's own
        #report-content swapped inside the shell's) appeared in the live DOM
        after the swap, which the test client cannot observe."""
        content = self.full_page().content.decode()

        self.assertEqual(content.count(REPORT_CONTENT_ID), 1)

    def test_the_shell_does_not_build_the_report(self):
        """The body is still deferred - inlining the skeleton must not pull the
        report's own work into the first request."""
        response = self.full_page()

        self.assertTemplateNotUsed(response, "partials/montrek_report_display.html")


class TestTheDataRequest(ReportLoadingTestCase):
    def test_it_returns_the_report_body(self):
        response = self.htmx_get(state="loading")

        self.assertTemplateUsed(response, "partials/montrek_report_display.html")

    def test_it_does_not_return_the_page_shell(self):
        content = self.htmx_get(state="loading").content.decode()

        self.assertNotIn("<html", content)


class TestTheSkeletonFallback(ReportLoadingTestCase):
    """An HTMX caller that asks without a state still gets the skeleton rather
    than a whole page injected into a fragment. Nothing in this project takes
    that route any more, which is exactly why it is pinned."""

    def test_it_returns_the_skeleton(self):
        response = self.htmx_get()

        self.assertTemplateUsed(response, "partials/montrek_report_loading.html")

    def test_the_skeleton_asks_for_the_report(self):
        content = self.htmx_get().content.decode()

        self.assertIn(LOADING_STATE_VALS, content)

    def test_it_is_not_a_whole_page(self):
        content = self.htmx_get().content.decode()

        self.assertNotIn("<html", content)
