from django.test import TestCase

from baseclasses.serializers import MontrekSerializer


class SerializerTest(TestCase):
    def test_serializer__no_repository(self):
        with self.assertRaises(NotImplementedError):
            MontrekSerializer()
