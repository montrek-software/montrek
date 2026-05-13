import unittest
from unittest.mock import MagicMock, patch

from file_export.views.file_export_views import FileExportTriggerView


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
