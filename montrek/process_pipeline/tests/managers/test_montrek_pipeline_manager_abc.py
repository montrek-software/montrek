import unittest
from unittest.mock import MagicMock, patch

from process_pipeline.tests.mocks import (
    SESSION_DATA,
    ConcreteTestManager,
    ConcreteTestManagerBroken,
    ConcreteTestManagerFailPostCheck,
    ConcreteTestManagerFailPreCheck,
    ConcreteTestManagerFailProcess,
)


class TestTriggerPipelineSync(unittest.TestCase):
    def setUp(self):
        self.manager = ConcreteTestManager(SESSION_DATA)

    def test_stores_registry_pk_in_session_data(self):
        self.manager.trigger_pipeline()
        self.assertIn(self.manager.registry_session_key, self.manager.session_data)
        self.assertEqual(
            self.manager.session_data[self.manager.registry_session_key], 1
        )

    def test_returns_true_on_success(self):
        self.assertTrue(self.manager.trigger_pipeline())

    def test_returns_false_when_process_fails(self):
        manager = ConcreteTestManagerFailPreCheck(SESSION_DATA)
        self.assertFalse(manager.trigger_pipeline())

    def test_sets_manager_message_on_success(self):
        self.manager.trigger_pipeline()
        self.assertEqual(self.manager.message, "post_check ok")

    def test_sets_manager_message_on_failure(self):
        manager = ConcreteTestManagerFailPreCheck(SESSION_DATA)
        manager.trigger_pipeline()
        self.assertEqual(manager.message, "Pre Check Failed")


class TestTriggerPipelineAsync(unittest.TestCase):
    def setUp(self):
        class MockTask:
            def __init__(self, manager_class):
                # Mock task to setup test
                pass

        class AsyncManager(ConcreteTestManager):
            do_process_async = True
            pipeline_task_class = MockTask

        self.manager = AsyncManager(SESSION_DATA)
        mock_task = MagicMock()
        mock_task.delay.return_value = MagicMock(id="task-abc")
        self.manager.pipeline_task = mock_task

    def test_returns_true_immediately(self):
        self.assertTrue(self.manager.trigger_pipeline())

    def test_dispatches_task_with_session_data_and_pipeline_data(self):
        pipeline_data = {"import_data": [1, 2, 3]}
        self.manager.trigger_pipeline(pipeline_data=pipeline_data)
        self.manager.pipeline_task.delay.assert_called_once_with(
            session_data=self.manager.session_data,
            pipeline_data=pipeline_data,
        )

    def test_stores_celery_task_id_in_registry(self):
        self.manager.trigger_pipeline()
        update_kwargs = self.manager._registry_updates[-1]
        self.assertEqual(update_kwargs.get("celery_task_id"), "task-abc")

    def test_sets_scheduled_message(self):
        self.manager.trigger_pipeline()
        self.assertIn("scheduled", self.manager.message.lower())

    def test_does_not_call_process_directly(self):
        with patch.object(self.manager, "process") as mock_process:
            self.manager.trigger_pipeline()
            mock_process.assert_not_called()


class TestProcessPipelineSteps(unittest.TestCase):
    def _run_process(self, manager_class):
        manager = manager_class(SESSION_DATA)
        manager.session_data[manager.registry_session_key] = 1
        manager.process()
        return manager

    def test_success_sets_status_processed(self):
        manager = self._run_process(ConcreteTestManager)
        statuses = [u.get("process_status") for u in manager._registry_updates]
        self.assertIn("processed", statuses)

    def test_success_sets_processor_message(self):
        manager = self._run_process(ConcreteTestManager)
        self.assertEqual(manager.message, "post_check ok")

    def test_success_sets_in_progress_before_processed(self):
        manager = self._run_process(ConcreteTestManager)
        statuses = [
            u.get("process_status")
            for u in manager._registry_updates
            if "process_status" in u
        ]
        self.assertEqual(statuses[0], "in_progress")
        self.assertEqual(statuses[-1], "processed")

    def test_pre_check_failure_sets_status_failed(self):
        manager = self._run_process(ConcreteTestManagerFailPreCheck)
        statuses = [u.get("process_status") for u in manager._registry_updates]
        self.assertIn("failed", statuses)

    def test_pre_check_failure_sets_processor_message(self):
        manager = self._run_process(ConcreteTestManagerFailPreCheck)
        self.assertEqual(manager.message, "Pre Check Failed")

    def test_pre_check_failure_returns_false(self):
        manager = ConcreteTestManagerFailPreCheck(SESSION_DATA)
        manager.session_data[manager.registry_session_key] = 1
        self.assertFalse(manager.process())

    def test_process_failure_sets_status_failed(self):
        manager = self._run_process(ConcreteTestManagerFailProcess)
        statuses = [u.get("process_status") for u in manager._registry_updates]
        self.assertIn("failed", statuses)

    def test_process_failure_sets_processor_message(self):
        manager = self._run_process(ConcreteTestManagerFailProcess)
        self.assertEqual(manager.message, "Process Failed")

    def test_post_check_failure_sets_status_failed(self):
        manager = self._run_process(ConcreteTestManagerFailPostCheck)
        statuses = [u.get("process_status") for u in manager._registry_updates]
        self.assertIn("failed", statuses)

    def test_post_check_failure_sets_processor_message(self):
        manager = self._run_process(ConcreteTestManagerFailPostCheck)
        self.assertEqual(manager.message, "Post Check Failed")


class TestSetStatus(unittest.TestCase):
    def setUp(self):
        self.manager = ConcreteTestManager(SESSION_DATA)
        self.manager._load_registry()

    def test_uses_status_field_name(self):
        self.manager._set_status("processed", "all good")
        update = self.manager._registry_updates[-1]
        self.assertIn("process_status", update)
        self.assertEqual(update["process_status"], "processed")

    def test_uses_message_field_name(self):
        self.manager._set_status("failed", "something broke")
        update = self.manager._registry_updates[-1]
        self.assertIn("process_message", update)
        self.assertEqual(update["process_message"], "something broke")

    def test_empty_message_default(self):
        self.manager._set_status("processed")
        update = self.manager._registry_updates[-1]
        self.assertEqual(update["process_message"], "")


class TestManagerDefaults(unittest.TestCase):
    def setUp(self):
        self.manager = ConcreteTestManager(SESSION_DATA)

    def test_additional_registry_data_returns_empty_dict(self):
        self.assertEqual(self.manager.additional_registry_data(), {})

    def test_on_pipeline_success_is_noop(self):
        self.manager._on_pipeline_success()  # must not raise

    def test_registry_is_none_before_load(self):
        self.assertIsNone(self.manager.registry)

    def test_message_is_empty_on_init(self):
        self.assertEqual(self.manager.message, "")


class TestBrokenProcess(unittest.TestCase):
    def setUp(self):
        self.manager = ConcreteTestManagerBroken(SESSION_DATA)
        self.manager._load_registry()

    def test_catch_broken_process(self):
        self.manager.process()
        update = self.manager._registry_updates[-1]
        self.assertIn("process_status", update)
        self.assertEqual(update["process_status"], "failed")
        self.assertEqual(update["process_message"], "ERROR: Simulated Error")
