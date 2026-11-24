from collections.abc import Sequence
from dataclasses import dataclass, field


@dataclass
class MarkdownTable:
    """A GitHub flavoured Markdown table, as Forgejo and GitHub render it.

    ``right_aligned`` holds the indices of the columns aligned right, e.g.
    those of numbers. Without ``headers`` the header row stays empty, as for
    a block of labels and values.
    """

    rows: Sequence[Sequence[str]]
    headers: Sequence[str] = ()
    right_aligned: frozenset[int] = field(default_factory=frozenset)

    def to_markdown(self) -> str:
        column_count = len(self.headers) or max(
            (len(row) for row in self.rows), default=0
        )
        if not column_count:
            return ""
        headers = list(self.headers) or [""] * column_count
        lines = [
            self._line(self.escape_cell(header) for header in headers),
            self._line(
                "---:" if index in self.right_aligned else "---"
                for index in range(column_count)
            ),
        ]
        for row in self.rows:
            cells = list(row) + [""] * (column_count - len(row))
            lines.append(self._line(self.escape_cell(cell) for cell in cells))
        return "\n".join(lines) + "\n"

    @staticmethod
    def _line(cells) -> str:
        return "| " + " | ".join(cells) + " |"

    @staticmethod
    def escape_cell(text: str) -> str:
        """A pipe would end the cell and a line break the row."""
        text = text.replace("|", "\\|").strip()
        return "<br>".join(line.strip() for line in text.splitlines())
