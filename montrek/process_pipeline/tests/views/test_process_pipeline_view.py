import unittest
from unittest.mock import patch

from process_pipeline.views.process_pipeline_view import ProcessPipelineViewABC


class ConcreteView(ProcessPipelineViewABC):
    success_url = "montrek_example_a_list"

    def process(self):
        # Mock task to setup test
        pass

    def show_messages(self):
        # Mock task to setup test
        pass


class TestProcessPipelineViewABCProcess(unittest.TestCase):
    def test_process_raises_not_implemented(self):
        view = ProcessPipelineViewABC()
        with self.assertRaises(NotImplementedError):
            view.process()

    def test_error_message_is_descriptive(self):
        view = ProcessPipelineViewABC()
        with self.assertRaises(NotImplementedError) as exc_info:
            view.process()
        self.assertIn("process", str(exc_info.exception).lower())


class TestProcessPipelineViewABCGetRedirectUrl(unittest.TestCase):
    def test_get_redirect_url_calls_process(self):
        view = ConcreteView()
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

    def test_get_redirect_url_calls_show_messages(self):
        view = ConcreteView()
        with (
            patch.object(view, "process"),
            patch.object(view, "show_messages") as mock_show,
            patch(
                "process_pipeline.views.process_pipeline_view.reverse",
                return_value="/list/",
            ),
        ):
            view.get_redirect_url()
            mock_show.assert_called_once()

    def test_get_redirect_url_returns_reversed_success_url(self):
        view = ConcreteView()
        with (
            patch.object(view, "process"),
            patch.object(view, "show_messages"),
            patch(
                "process_pipeline.views.process_pipeline_view.reverse",
                return_value="/a/list/",
            ) as mock_reverse,
        ):
            result = view.get_redirect_url()
            mock_reverse.assert_called_once_with(ConcreteView.success_url)
            self.assertEqual(result, "/a/list/")
