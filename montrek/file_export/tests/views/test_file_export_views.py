import unittest
from unittest.mock import MagicMock, patch

from django import forms

from file_export.views.file_export_views import (
    FileExportFormView,
    FileExportTriggerView,
)


class ConcreteExportTriggerView(FileExportTriggerView):
    success_url = "montrek_example_a_list"


class TestFileExportTriggerViewProcess(unittest.TestCase):
    def test_process_calls_trigger_export(self):
        view = ConcreteExportTriggerView()
        view.manager_class = MagicMock()
        mock_manager = MagicMock()
        mock_manager.message = ""
        view._manager = mock_manager

        view.process()

        mock_manager.trigger_export.assert_called_once()

    def test_get_redirect_url_calls_process(self):
        view = ConcreteExportTriggerView()
        with (
            patch.object(view, "process") as mock_process,
            patch.object(view, "show_messages"),
            patch(
                "process_pipeline.views.process_pipeline_view.reverse",
                return_value="/list/",
            ),
        ):
            view.get_redirect_url()
            mock_process.assert_called_once()

    def test_get_redirect_url_returns_success_url(self):
        view = ConcreteExportTriggerView()
        with (
            patch.object(view, "process"),
            patch.object(view, "show_messages"),
            patch(
                "process_pipeline.views.process_pipeline_view.reverse",
                return_value="/a/list/",
            ) as mock_reverse,
        ):
            result = view.get_redirect_url()
            mock_reverse.assert_called_once_with(ConcreteExportTriggerView.success_url)
            self.assertEqual(result, "/a/list/")


class ExportChoiceForm(forms.Form):
    """Stands in for a real export form: one required field, one optional."""

    report = forms.ChoiceField(choices=[("summary", "Summary")])
    note = forms.CharField(required=False)


class ConcreteExportFormView(FileExportFormView):
    export_form_class = ExportChoiceForm
    success_url = "/exports/"

    def get_pipeline_data(self, form) -> dict:
        return {"report": form.cleaned_data["report"]}

    def get_success_url(self) -> str:
        return self.success_url


def _build_view(trigger_result: bool = True) -> ConcreteExportFormView:
    view = ConcreteExportFormView()
    manager = MagicMock()
    manager.message = "Export successful"
    manager.trigger_export.return_value = trigger_result
    view._manager = manager
    return view


def _post_request(data: dict) -> MagicMock:
    request = MagicMock()
    request.POST = data
    request.FILES = {}
    return request


class TestFileExportFormViewValidPost(unittest.TestCase):
    def test_pipeline_data_is_forwarded_to_trigger_export(self):
        view = _build_view()
        request = _post_request({"report": "summary"})

        with patch("file_export.views.file_export_views.messages"):
            view.post(request)

        view.manager.trigger_export.assert_called_once_with(
            pipeline_data={"report": "summary"}
        )

    def test_redirects_to_success_url(self):
        view = _build_view()
        request = _post_request({"report": "summary"})

        with patch("file_export.views.file_export_views.messages"):
            response = view.post(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/exports/")

    def test_success_is_reported_as_info(self):
        view = _build_view(trigger_result=True)
        request = _post_request({"report": "summary"})

        with patch("file_export.views.file_export_views.messages") as mock_messages:
            view.post(request)

        mock_messages.info.assert_called_once_with(request, "Export successful")
        mock_messages.error.assert_not_called()

    def test_failure_is_reported_as_error(self):
        view = _build_view(trigger_result=False)
        view.manager.message = "Export failed"
        request = _post_request({"report": "summary"})

        with patch("file_export.views.file_export_views.messages") as mock_messages:
            view.post(request)

        mock_messages.error.assert_called_once_with(request, "Export failed")
        mock_messages.info.assert_not_called()


class TestFileExportFormViewInvalidPost(unittest.TestCase):
    def setUp(self):
        self.view = _build_view()
        self.request = _post_request({"report": "not-a-choice"})
        self.rendered = {}

        def capture(context):
            self.rendered = context
            return "rendered"

        patcher = patch.object(self.view, "render_to_response", side_effect=capture)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher_context = patch.object(
            self.view, "get_context_data", side_effect=self.view.get_template_context
        )
        patcher_context.start()
        self.addCleanup(patcher_context.stop)

    def test_does_not_trigger_the_export(self):
        self.view.post(self.request)
        self.view.manager.trigger_export.assert_not_called()

    def test_rerenders_the_bound_form_with_its_errors(self):
        self.view.post(self.request)
        form = self.rendered["export_form"]
        self.assertTrue(form.is_bound)
        self.assertIn("report", form.errors)

    def test_rerendered_form_keeps_the_submitted_values(self):
        self.view.post(self.request)
        form = self.rendered["export_form"]
        self.assertEqual(form.data["report"], "not-a-choice")
