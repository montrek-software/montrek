import unittest

from process_pipeline.managers.process_pipeline_processor_abc import (
    PipelineProcessorABC,
)


class ConcreteProcessor(PipelineProcessorABC):
    def pre_check(self) -> bool:
        return True

    def process(self) -> bool:
        return True

    def post_check(self) -> bool:
        return True


class TestPipelineProcessorABCMessage(unittest.TestCase):
    def setUp(self):
        self.processor = ConcreteProcessor()

    def test_message_is_empty_on_init(self):
        self.assertEqual(self.processor.message, "")

    def test_set_message_updates_message(self):
        self.processor.set_message("hello")
        self.assertEqual(self.processor.message, "hello")

    def test_set_message_overwrites_previous(self):
        self.processor.set_message("first")
        self.processor.set_message("second")
        self.assertEqual(self.processor.message, "second")

    def test_message_is_per_instance(self):
        other = ConcreteProcessor()
        self.processor.set_message("mine")
        self.assertEqual(other.message, "")


class TestPipelineProcessorABCSendMail(unittest.TestCase):
    def test_send_mail_is_true_by_default(self):
        self.assertTrue(ConcreteProcessor.send_mail)

    def test_send_mail_overridable_at_class_level(self):
        class NoMailProcessor(PipelineProcessorABC):
            send_mail = False

            def pre_check(self):
                return True

            def process(self):
                return True

            def post_check(self):
                return True

        self.assertFalse(NoMailProcessor().send_mail)


class TestPipelineProcessorABCNotImplemented(unittest.TestCase):
    def setUp(self):
        class NoStepsProcessor(PipelineProcessorABC):
            pass

        self.processor = NoStepsProcessor()

    def test_pre_check_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.processor.pre_check()

    def test_process_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.processor.process()

    def test_post_check_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.processor.post_check()

    def test_error_message_includes_class_name(self):
        try:
            self.processor.pre_check()
        except NotImplementedError as e:
            self.assertIn("NoStepsProcessor", str(e))
