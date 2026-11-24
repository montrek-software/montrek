from collections.abc import Iterable
from typing import Any

from reporting.core.text_converter import HtmlMarkdownConverter


class ReportElementMarkdown:
    """Markdown of any report element.

    Elements of other apps need not implement ``to_markdown()``: their HTML
    is converted instead, which keeps the text and drops the layout.
    """

    @staticmethod
    def convert(element: Any) -> str:
        if hasattr(element, "to_markdown"):
            return element.to_markdown()
        return HtmlMarkdownConverter.convert(element.to_html())

    @staticmethod
    def join(parts: Iterable[str]) -> str:
        """The parts as blocks separated by a blank line, empty ones left out.

        Only the line breaks around a part are trimmed: its indentation can
        carry meaning, e.g. that of an indented code block.
        """
        blocks = (part.strip("\r\n") for part in parts if part.strip())
        return "\n\n".join(blocks)
