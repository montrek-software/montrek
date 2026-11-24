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
