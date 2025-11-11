import sys
from pathlib import Path


class DocsFilesMixin:
    def get_docs_path(self) -> Path:
        module = sys.modules[self.__class__.__module__]
        module_file = Path(str(module.__file__)).resolve()
        return module_file.parent.parent / "docs"
