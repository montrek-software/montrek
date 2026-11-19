from django.test import SimpleTestCase

from baseclasses.dataclasses.montrek_message import (
    MontrekMessageError,
    MontrekMessageInfo,
)
from baseclasses.managers.montrek_manager import MontrekManager


class TestAddMessage(SimpleTestCase):
    def test_adds_the_message(self):
        manager = MontrekManager()
        manager.add_message(MontrekMessageError("Failed"))
        self.assertEqual(manager.messages, [MontrekMessageError("Failed")])

    def test_adds_the_same_message_once(self):
        manager = MontrekManager()
        manager.add_message(MontrekMessageError("Failed"))
        manager.add_message(MontrekMessageError("Failed"))
        self.assertEqual(manager.messages, [MontrekMessageError("Failed")])

    def test_adds_messages_that_differ_in_text_or_type(self):
        manager = MontrekManager()
        messages = [
            MontrekMessageError("Failed"),
            MontrekMessageError("Failed again"),
            MontrekMessageInfo("Failed"),
        ]
        for message in messages:
            manager.add_message(message)
        self.assertEqual(manager.messages, messages)
