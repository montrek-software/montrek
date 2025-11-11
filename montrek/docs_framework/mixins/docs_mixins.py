import os
import sys
from pathlib import Path


class DocsFilesMixin:
    allowed_file_types = [".md"]

    def get_docs_path(self) -> Path:
        module = sys.modules[self.__class__.__module__]
        module_file = Path(str(module.__file__)).resolve()
        return module_file.parent.parent / "docs"

    def get_docs_files(self) -> list[Path]:
        docs_path = self.get_docs_path()
        if not docs_path.exists():
            return []

        docs_files = []
        for filename in os.listdir(docs_path):
            file_path = docs_path / filename
            if file_path.is_file() and file_path.suffix in self.allowed_file_types:
                docs_files.append(file_path)

        return docs_files
