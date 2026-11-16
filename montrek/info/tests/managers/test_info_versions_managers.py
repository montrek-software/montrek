import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from django.test import TestCase
from info.modules.release_info import ReleaseInfo
from info.tests.mocks import MockInfoVersionsManager
from info.tests.modules.test_release_info import MANIFEST


class TestInfoVersionsManager(TestCase):
    def test_git_versions(self):
        manager = MockInfoVersionsManager({})
        git_versions_manager = manager.get_git_versions()
        pd.testing.assert_frame_equal(
            git_versions_manager.df,
            pd.DataFrame({"repository": ["A", "B", "C", "A", "B", "C"]}),
        )


class TestInfoVersionsManagerRelease(TestCase):
    def test_release_versions_replace_git_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "release.json"
            manifest.write_text(json.dumps(MANIFEST))
            manager = MockInfoVersionsManager({})
            with patch.object(
                MockInfoVersionsManager,
                "get_release_info",
                return_value=ReleaseInfo(manifest),
            ):
                manager.collect_report_elements()
        self.assertEqual(len(manager.report_elements), 1)
        df = manager.report_elements[0].df
        self.assertEqual(df["ref"].tolist()[:2], ["v1.1.106", "v1.0.5"])

    def test_git_versions_without_manifest(self):
        manager = MockInfoVersionsManager({})
        with patch.object(
            MockInfoVersionsManager,
            "get_release_info",
            return_value=ReleaseInfo(Path("/nonexistent/release.json")),
        ):
            manager.collect_report_elements()
        self.assertEqual(
            manager.report_elements[0].df["repository"].tolist()[:3], ["A", "B", "C"]
        )
