import socket
from django.test import LiveServerTestCase
from montrek.testing.test_runner import guarded_socket, real_socket


class MontrekLiveServerTestCase(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        socket.socket = real_socket
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        socket.socket = guarded_socket
        super().tearDownClass()
