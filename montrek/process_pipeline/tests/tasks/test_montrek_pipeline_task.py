from unittest.mock import patch

from django.test import TestCase
from testing.decorators.add_logged_in_user import add_logged_in_user

from process_pipeline.tests.mocks import (
    ConcreteTestManager,
    MockProcessor,
)


def _make_task(manager_class=ConcreteTestManager):
    """Instantiate MontrekPipelineTask, patching Celery registration to avoid name conflicts."""
    from process_pipeline.tasks.montrek_pipeline_task import MontrekPipelineTask

    with (
        patch("tasks.montrek_task.celery_app.register_task"),
        patch.object(MontrekPipelineTask, "raise_for_conflicting_task_name"),
    ):
        return MontrekPipelineTask(manager_class)


class TestMontrekPipelineTaskInit(TestCase):
    def test_task_name_includes_manager_module(self):
        task = _make_task()
        self.assertIn(ConcreteTestManager.__module__, task.name)

    def test_task_name_includes_manager_class_name(self):
        task = _make_task()
        self.assertIn(ConcreteTestManager.__name__, task.name)

    def test_task_name_ends_with_pipeline_task(self):
        task = _make_task()
        self.assertTrue(task.name.endswith("_pipeline_task"))

    def test_manager_class_stored(self):
        task = _make_task()
        self.assertIs(task.manager_class, ConcreteTestManager)


class TestMontrekPipelineTaskRun(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.task = _make_task()
        self.session_data = {"user_id": self.user.id}
        self.session_data[ConcreteTestManager.registry_session_key] = 1

    def test_run_calls_process_on_manager(self):
        with (
            patch.object(
                ConcreteTestManager, "process", return_value=True
            ) as mock_process,
            patch.object(self.task, "_send_result_mail"),
        ):
            self.task.run(self.session_data)
            mock_process.assert_called_once_with(pipeline_data={})

    def test_run_forwards_pipeline_data(self):
        data = {"import_data": [1, 2, 3]}
        with (
            patch.object(
                ConcreteTestManager, "process", return_value=True
            ) as mock_process,
            patch.object(self.task, "_send_result_mail"),
        ):
            self.task.run(self.session_data, pipeline_data=data)
            mock_process.assert_called_once_with(pipeline_data=data)

    def test_run_returns_manager_message(self):
        with (
            patch.object(ConcreteTestManager, "process", return_value=True),
            patch.object(self.task, "_send_result_mail"),
        ):
            result = self.task.run(self.session_data)
            self.assertIsInstance(result, str)

    def test_run_calls_send_result_mail(self):
        with (
            patch.object(ConcreteTestManager, "process", return_value=True),
            patch.object(self.task, "_send_result_mail") as mock_mail,
        ):
            self.task.run(self.session_data)
            mock_mail.assert_called_once()

    def test_run_none_pipeline_data_defaults_to_empty_dict(self):
        with (
            patch.object(
                ConcreteTestManager, "process", return_value=True
            ) as mock_process,
            patch.object(self.task, "_send_result_mail"),
        ):
            self.task.run(self.session_data, pipeline_data=None)
            mock_process.assert_called_once_with(pipeline_data={})


class TestMontrekPipelineTaskMail(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.task = _make_task()
        self.session_data = {"user_id": self.user.id}
        self.task.manager = ConcreteTestManager(self.session_data)
        self.task.manager.processor = MockProcessor()
        self.task.manager.message = "all done"

    def test_send_result_mail_success_subject(self):
        with (
            patch.object(
                self.task.mailing_manager_class, "send_montrek_mail"
            ) as mock_send,
            patch("django.contrib.auth.get_user_model") as mock_get_user,
        ):
            mock_get_user.return_value.objects.get.return_value = self.user
            self.task._send_result_mail(self.session_data, result=True)
            subject = mock_send.call_args[0][1]
            self.assertNotIn("ERROR", subject)
            self.assertIn("successful", subject)

    def test_send_result_mail_failure_subject_has_error_prefix(self):
        with (
            patch.object(
                self.task.mailing_manager_class, "send_montrek_mail"
            ) as mock_send,
            patch("django.contrib.auth.get_user_model") as mock_get_user,
        ):
            mock_get_user.return_value.objects.get.return_value = self.user
            self.task._send_result_mail(self.session_data, result=False)
            subject = mock_send.call_args[0][1]
            self.assertTrue(subject.startswith("ERROR"))

    def test_do_send_mail_false_skips_mail(self):
        self.task.do_send_mail = False
        with patch.object(
            self.task.mailing_manager_class, "send_montrek_mail"
        ) as mock_send:
            self.task._send_result_mail(self.session_data, result=True)
            mock_send.assert_not_called()


class TestMontrekPipelineTaskSubject(TestCase):
    def setUp(self):
        self.task = _make_task()

    def test_get_subject_success(self):
        subject = self.task._get_subject(result=True)
        self.assertIn("successful", subject)
        self.assertNotIn("ERROR", subject)

    def test_get_subject_failure(self):
        subject = self.task._get_subject(result=False)
        self.assertTrue(subject.startswith("ERROR"))
        self.assertIn("unsuccessful", subject)

    def test_message_name_converts_camel_case(self):
        name = self.task._message_name()
        self.assertIn(" ", name)
        self.assertNotEqual(name, ConcreteTestManager.__name__)

    def test_get_subject_includes_manager_name(self):
        name = self.task._message_name()
        subject = self.task._get_subject(result=True)
        self.assertIn(name, subject)


class TestMontrekPipelineTaskRecipients(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.task = _make_task()
        self.session_data = {"user_id": self.user.id}

    def test_recipients_returns_list_with_one_user(self):
        recipients = self.task.recipients(self.session_data)
        self.assertEqual(len(recipients), 1)

    def test_recipients_returns_correct_user(self):
        recipients = self.task.recipients(self.session_data)
        self.assertEqual(recipients[0].id, self.user.id)
