from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocsFile:
    docs_path: Path

    @property
    def docs_name(self) -> str:
        return self.docs_path.stem

    @property
    def docs_title(self) -> str:
        return self.docs_name.replace("_", " ").title()
