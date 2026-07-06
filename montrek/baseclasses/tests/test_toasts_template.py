from django.template.loader import render_to_string
from django.test import TestCase


class FakeMessage:
    def __init__(self, tags: str, text: str):
        self.tags = tags
        self.text = text

    def __str__(self) -> str:
        return self.text


class TestToastsTemplate(TestCase):
    def render_toasts(self, *messages) -> str:
        return render_to_string("partials/toasts.html", {"messages": messages})

    def test_error_renders_persistent_danger_toast(self):
        html = self.render_toasts(FakeMessage("error", "Something broke"))
        self.assertIn("mt-toast-danger", html)
        self.assertIn('data-bs-autohide="false"', html)
        self.assertIn("bi-x-circle-fill", html)
        self.assertIn("Something broke", html)

    def test_warning_renders_persistent_warning_toast(self):
        html = self.render_toasts(FakeMessage("warning", "Careful"))
        self.assertIn("mt-toast-warning", html)
        self.assertIn('data-bs-autohide="false"', html)
        self.assertIn("bi-exclamation-triangle-fill", html)

    def test_info_renders_auto_dismissing_success_toast(self):
        html = self.render_toasts(FakeMessage("info", "Saved"))
        self.assertIn("mt-toast-success", html)
        self.assertIn("data-bs-delay", html)
        self.assertNotIn('data-bs-autohide="false"', html)
        self.assertIn("bi-check-circle-fill", html)

    def test_success_renders_auto_dismissing_success_toast(self):
        html = self.render_toasts(FakeMessage("success", "Done"))
        self.assertIn("mt-toast-success", html)
        self.assertIn("data-bs-delay", html)
        self.assertNotIn('data-bs-autohide="false"', html)

    def test_no_messages_renders_empty_container(self):
        html = self.render_toasts()
        # The container is always present so it can be targeted by HTMX
        # out-of-band swaps, but it holds no toasts.
        self.assertIn('id="mt-toast-container"', html)
        self.assertNotIn('role="alert"', html)

    def test_container_has_stable_oob_target_id(self):
        html = self.render_toasts(FakeMessage("info", "Saved"))
        # Stable id lets an HTMX partial refresh the toasts out-of-band.
        self.assertIn('id="mt-toast-container"', html)

    def test_one_toast_per_message(self):
        html = self.render_toasts(
            FakeMessage("info", "First"),
            FakeMessage("error", "Second"),
        )
        self.assertEqual(html.count('role="alert"'), 2)
        self.assertIn("First", html)
        self.assertIn("Second", html)
