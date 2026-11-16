import json
from pathlib import Path

import pandas as pd


class ReleaseInfo:
    """
    The versions an image was built from.

    A client image has no .git directories. Its build (montrek-deploy
    release_source.py) writes release.json next to manage.py instead: the
    release name, core and every extension with repo, tag and commit, and the
    sha256 of the locked requirements. /montrek/.montrek-image holds the commit
    of the deployment repository the image was built from.
    """

    def __init__(self, manifest_path: Path, image_marker_path: Path | None = None):
        self.manifest_path = manifest_path
        self.image_marker_path = image_marker_path

    def exists(self) -> bool:
        return self.manifest_path.is_file()

    def to_dataframe(self) -> pd.DataFrame:
        manifest = json.loads(self.manifest_path.read_text())
        rows = [self._row("montrek", manifest["core"])]
        rows += [self._row(ext["name"], ext) for ext in manifest.get("extensions", [])]
        rows.append(
            {
                "repo_name": f"{manifest.get('name', 'release')} (deployment)",
                "ref": "",
                "commit_hash": self._image_revision(),
                "remote_url": "",
            }
        )
        return pd.DataFrame(rows)

    @staticmethod
    def _row(name: str, source: dict) -> dict:
        return {
            "repo_name": name,
            "ref": source.get("ref", ""),
            "commit_hash": source.get("commit", ""),
            "remote_url": source.get("repo", ""),
        }

    def _image_revision(self) -> str:
        if self.image_marker_path and self.image_marker_path.is_file():
            return self.image_marker_path.read_text().strip() or "unknown"
        return "unknown"
