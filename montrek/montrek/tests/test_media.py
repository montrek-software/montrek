from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from user.tests.factories.montrek_user_factories import MontrekUserFactory


# Cleared, so the tests stream by default even where compose sets it.
@override_settings(MEDIA_X_ACCEL_REDIRECT="")
class TestServeMedia(TestCase):
    def setUp(self):
        self.media_root = Path(settings.MEDIA_ROOT)
        self.file = self.media_root / "media_test" / "report 1.txt"
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text("content")
        self.addCleanup(self.file.unlink)
        self.url = reverse("media", args=["media_test/report 1.txt"])

    def login(self):
        self.client.force_login(MontrekUserFactory())

    def test_redirects_to_login_without_session(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, settings.LOGIN_URL, fetch_redirect_response=False
        )

    def test_rest_api_parameter_does_not_open_uploads(self):
        response = self.client.get(self.url, {"gen_rest_api": "true"})
        self.assertRedirects(
            response, settings.LOGIN_URL, fetch_redirect_response=False
        )

    def test_streams_file_to_logged_in_user(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"content")
        self.assertIn("private", response["Cache-Control"])
        self.assertNotIn("X-Accel-Redirect", response)

    @override_settings(MEDIA_X_ACCEL_REDIRECT="/protected-uploads/")
    def test_hands_file_to_nginx_when_configured(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        self.assertEqual(
            response["X-Accel-Redirect"],
            "/protected-uploads/media_test/report%201.txt",
        )
        self.assertEqual(response["Content-Type"], "text/plain")

    @override_settings(LOGIN_EXEMPT_PATHS=[r"^uploads/media_test/.*$"])
    def test_exempt_path_is_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("public", response["Cache-Control"])

    def test_missing_file_and_directory_are_not_found(self):
        self.login()
        for path in ("media_test/missing.txt", "media_test", "media_test/"):
            with self.subTest(path):
                response = self.client.get(reverse("media", args=[path]))
                self.assertEqual(response.status_code, 404)

    def test_paths_outside_media_root_are_not_found(self):
        self.login()
        outside = self.media_root.parent / "outside_media.txt"
        outside.write_text("secret")
        self.addCleanup(outside.unlink)
        for path in ("../outside_media.txt", "media_test/../../outside_media.txt"):
            with self.subTest(path):
                response = self.client.get(f"{settings.MEDIA_URL}{path}")
                self.assertEqual(response.status_code, 404)

    @override_settings(LOGIN_EXEMPT_PATHS=[r"^uploads/media_test/.*$"])
    def test_dot_segments_do_not_leave_a_public_prefix(self):
        private = self.media_root / "media_private" / "private.csv"
        private.parent.mkdir(exist_ok=True)
        private.write_text("private")
        self.addCleanup(private.unlink)
        for path in (
            "media_test/../media_private/private.csv",
            "media_test/./../media_private/private.csv",
        ):
            with self.subTest(path):
                response = self.client.get(f"{settings.MEDIA_URL}{path}")
                self.assertEqual(response.status_code, 404)

    def test_symlinks_out_of_media_root_are_not_followed(self):
        self.login()
        outside_dir = self.media_root.parent / "outside_media_dir"
        outside_dir.mkdir(exist_ok=True)
        outside = outside_dir / "secret.txt"
        outside.write_text("secret")
        self.addCleanup(outside_dir.rmdir)
        self.addCleanup(outside.unlink)
        links = {
            self.file.parent / "file_link.txt": outside,
            self.file.parent / "dir_link": outside_dir,
        }
        for link, target in links.items():
            link.symlink_to(target)
            self.addCleanup(link.unlink)
        for path in ("media_test/file_link.txt", "media_test/dir_link/secret.txt"):
            with self.subTest(path):
                response = self.client.get(reverse("media", args=[path]))
                self.assertEqual(response.status_code, 404)

    def test_symlinks_within_media_root_are_served(self):
        self.login()
        link = self.file.parent / "inner_link.txt"
        link.symlink_to(self.file)
        self.addCleanup(link.unlink)
        response = self.client.get(reverse("media", args=["media_test/inner_link.txt"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"content")

    def test_only_safe_methods(self):
        self.login()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 405)
