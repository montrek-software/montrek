import json
import tempfile
from pathlib import Path

from django.test import SimpleTestCase
from info.modules.release_info import ReleaseInfo

MANIFEST = {
    "name": "business",
    "core": {
        "repo": "https://github.com/montrek-software/montrek.git",
        "ref": "v1.1.106",
        "commit": "abc123",
    },
    "extensions": [
        {
            "name": "mt_crm",
            "repo": "https://forgejo.example/mt_crm.git",
            "ref": "v1.0.5",
            "commit": "def456",
        }
    ],
    "requirements_sha256": "0" * 64,
}


class TestReleaseInfo(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.manifest = self.dir / "release.json"
        self.marker = self.dir / ".montrek-image"

    def test_missing_manifest(self):
        self.assertFalse(ReleaseInfo(self.manifest, self.marker).exists())

    def test_versions_from_manifest(self):
        self.manifest.write_text(json.dumps(MANIFEST))
        self.marker.write_text("feedbeef\n")
        info = ReleaseInfo(self.manifest, self.marker)
        self.assertTrue(info.exists())
        df = info.to_dataframe()
        self.assertEqual(
            df["repo_name"].tolist(), ["montrek", "mt_crm", "business (deployment)"]
        )
        self.assertEqual(df["ref"].tolist(), ["v1.1.106", "v1.0.5", ""])
        self.assertEqual(df["commit_hash"].tolist(), ["abc123", "def456", "feedbeef"])

    def test_without_image_marker(self):
        self.manifest.write_text(json.dumps(MANIFEST))
        df = ReleaseInfo(self.manifest, self.marker).to_dataframe()
        self.assertEqual(df["commit_hash"].iloc[-1], "unknown")
