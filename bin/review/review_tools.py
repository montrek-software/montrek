"""Read-only tools the review model calls to explore the codebase."""

from __future__ import annotations

import json
import re
from typing import Any

from review_scope import ReviewScope

MAX_OUTPUT_CHARS = 15_000
MAX_READ_LINES = 400
MAX_LISTED_FILES = 300


class ReviewTools:
    """Tool definitions in the chat-completions format, and their execution.

    Tools only ever open paths from ``ReviewScope.visible_files``; a path the
    model makes up is looked up in that set, never resolved on disk, so there is
    no way to step outside it.
    """

    def __init__(self, scope: ReviewScope) -> None:
        self.scope = scope
        self.files = sorted(scope.visible_files)

    @property
    def definitions(self) -> list[dict[str, Any]]:
        return [
            self._definition(
                "list_files",
                "List the files under a directory, e.g. 'montrek/baseclasses/'. "
                "An empty prefix lists the top-level directories.",
                {"prefix": {"type": "string", "description": "Directory prefix."}},
                [],
            ),
            self._definition(
                "read_file",
                f"Read a file with line numbers, at most {MAX_READ_LINES} lines "
                "per call.",
                {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer", "description": "1-based."},
                    "end_line": {"type": "integer", "description": "Inclusive."},
                },
                ["path"],
            ),
            self._definition(
                "search",
                "Search file contents with a Python regular expression. Use it to "
                "find callers, definitions, similar code and existing helpers.",
                {
                    "pattern": {"type": "string"},
                    "prefix": {
                        "type": "string",
                        "description": "Only search under this directory.",
                    },
                    "glob_suffix": {
                        "type": "string",
                        "description": "Only files ending in this, e.g. '.py'.",
                    },
                },
                ["pattern"],
            ),
        ]

    def execute(self, name: str, raw_arguments: str) -> str:
        try:
            arguments = json.loads(raw_arguments or "{}")
        except json.JSONDecodeError as error:
            return f"Error: arguments are not valid JSON ({error})."
        handlers = {
            "list_files": self.list_files,
            "read_file": self.read_file,
            "search": self.search,
        }
        handler = handlers.get(name)
        if handler is None:
            return f"Error: unknown tool '{name}'."
        try:
            output = handler(**arguments)
        except TypeError as error:
            return f"Error: bad arguments for {name} ({error})."
        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\n[output truncated]"
        return output

    def list_files(self, prefix: str = "") -> str:
        prefix = prefix.strip("/") + "/" if prefix.strip("/") else ""
        entries: set[str] = set()
        for path in self.files:
            if path.startswith(prefix):
                rest = path[len(prefix) :]
                entries.add(rest.split("/", 1)[0] + ("/" if "/" in rest else ""))
        if not entries:
            return f"No visible files under '{prefix}'."
        listed = sorted(entries)
        suffix = ""
        if len(listed) > MAX_LISTED_FILES:
            suffix = f"\n[{len(listed) - MAX_LISTED_FILES} more entries]"
        return "\n".join(listed[:MAX_LISTED_FILES]) + suffix

    def read_file(
        self, path: str, start_line: int = 1, end_line: int | None = None
    ) -> str:
        path = path.removeprefix("./")
        if path not in self.scope.visible_files:
            return f"Error: '{path}' is not a visible file. Use list_files or search."
        lines = (self.scope.project_root / path).read_text(errors="replace").split("\n")
        start = max(start_line, 1)
        end = min(end_line or len(lines), len(lines), start + MAX_READ_LINES - 1)
        numbered = [f"{n:>5}  {lines[n - 1]}" for n in range(start, end + 1)]
        note = ""
        if end < len(lines):
            note = f"\n[lines {end + 1}-{len(lines)} not shown]"
        return (
            f"{path} (lines {start}-{end} of {len(lines)})\n"
            + "\n".join(numbered)
            + note
        )

    def search(self, pattern: str, prefix: str = "", glob_suffix: str = "") -> str:
        try:
            regex = re.compile(pattern)
        except re.error as error:
            return f"Error: invalid regular expression ({error})."
        prefix = prefix.removeprefix("./")
        matches: list[str] = []
        for path in self.files:
            if not path.startswith(prefix) or not path.endswith(glob_suffix):
                continue
            text = (self.scope.project_root / path).read_text(errors="replace")
            for number, line in enumerate(text.split("\n"), start=1):
                if regex.search(line):
                    matches.append(f"{path}:{number}: {line.strip()[:200]}")
        if not matches:
            return "No matches."
        shown = matches[:100]
        rest = len(matches) - len(shown)
        return "\n".join(shown) + (f"\n[{rest} more matches]" if rest else "")

    @staticmethod
    def _definition(
        name: str,
        description: str,
        properties: dict[str, Any],
        required: list[str],
    ) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
