import tempfile
from pathlib import Path

from django.test import SimpleTestCase, override_settings


class TestStaticFilesWithoutNginx(SimpleTestCase):
    """Gunicorn serves STATIC_ROOT itself where no nginx sits in front."""

    def setUp(self):
        super().setUp()
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.static_root = Path(temp_dir.name)
        (self.static_root / "css").mkdir()
        (self.static_root / "css" / "site.css").write_text("body { margin: 0; }")

    def test_serves_collected_file_without_login(self):
        # WhiteNoise reads STATIC_ROOT when the middleware is built, which the
        # test client does on its first request -- after the override applies.
        with override_settings(STATIC_ROOT=str(self.static_root)):
            response = self.client.get("/static/css/site.css")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"body { margin: 0; }")
        self.assertIn("max-age", response["Cache-Control"])
