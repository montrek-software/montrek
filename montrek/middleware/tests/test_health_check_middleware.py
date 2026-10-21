from unittest import mock

from django.db import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings


# The production settings a health check has to get past: an unknown host, plain
# HTTP with the https redirect on, and no session.
@override_settings(ALLOWED_HOSTS=["montrek.example"], SECURE_SSL_REDIRECT=True)
class TestLiveness(SimpleTestCase):
    # A SimpleTestCase fails any database query, so these also show that the
    # liveness check does not need the database.

    def test_answers_for_any_host_without_login(self):
        for path in ("/health/", "/health"):
            with self.subTest(path):
                response = self.client.get(path, HTTP_HOST="10.0.0.5:8000")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"status": "ok"})

    def test_other_paths_are_still_validated(self):
        with self.assertLogs("django.security.DisallowedHost", "ERROR"):
            response = self.client.get("/home", HTTP_HOST="10.0.0.5")
        self.assertEqual(response.status_code, 400)


@override_settings(ALLOWED_HOSTS=["montrek.example"], SECURE_SSL_REDIRECT=True)
class TestReadiness(TestCase):
    def test_ready_with_database(self):
        response = self.client.get("/health/ready/", HTTP_HOST="10.0.0.5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_unavailable_without_database(self):
        with (
            mock.patch(
                "middleware.health_check_middleware.connection.cursor",
                side_effect=OperationalError("connection refused"),
            ),
            self.assertLogs(level="ERROR") as logs,
        ):
            response = self.client.get("/health/ready/", HTTP_HOST="10.0.0.5")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertIn("database unreachable", logs.output[0])
