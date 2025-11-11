import os
import sys
from pathlib import Path

from docs_framework.dataclasses.docs_dataclasses import DocsFile


class DocsFilesMixin:
    allowed_file_types = [".md"]

    def get_docs_path(self) -> Path:
        module = sys.modules[self.__class__.__module__]
        module_file = Path(str(module.__file__)).resolve()
        return module_file.parent.parent / "docs"

    def get_docs_files(self) -> list[DocsFile]:
        docs_path = self.get_docs_path()
        if not docs_path.exists():
            return []

        docs_files = []
        for filename in os.listdir(docs_path):
            file_path = docs_path / filename
            if file_path.is_file() and file_path.suffix in self.allowed_file_types:
                docs_file = DocsFile(docs_path=file_path)
                docs_files.append(docs_file)
        return docs_files
