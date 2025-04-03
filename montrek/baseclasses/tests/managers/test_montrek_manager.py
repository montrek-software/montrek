from django.test import TestCase
from baseclasses.managers.montrek_manager import (
    MontrekManager,
    MontrekManagerNotImplemented,
)


class TestMontrekManager(TestCase):
    def test_not_implemented(self):
        self.assertRaises(NotImplementedError, MontrekManager().download)
        self.assertRaises(NotImplementedError, MontrekManager().get_filename)
        self.assertRaises(NotImplementedError, MontrekManagerNotImplemented)

    def test_collect_messages__no_repository(self):
        manager = MontrekManager()
        manager.collect_messages()
        self.assertEqual(manager.messages, [])
