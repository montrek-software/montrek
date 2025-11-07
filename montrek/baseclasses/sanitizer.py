from typing import Any

import bleach
from bleach.css_sanitizer import CSSSanitizer


class HtmlSanitizer:
    ALLOWED_TAGS = [
        "p",
        "b",
        "i",
        "u",
        "em",
        "strong",
        "a",
        "ul",
        "ol",
        "li",
        "br",
        "span",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "pre",
        "code",
        "table",
        "thead",
        "tbody",
        "th",
        "tr",
        "td",
    ]

    ALLOWED_ATTRIBUTES = {
        "*": ["class", "style"],
        "a": ["href", "title", "target"],
        "img": ["src", "alt"],
        "table": ["border"],
    }

    ALLOWED_STYLES = ["color", "font-weight", "text-align"]

    def __init__(self):
        # Apply allowed styles using the CSS sanitizer
        self.css_sanitizer = CSSSanitizer(allowed_css_properties=self.ALLOWED_STYLES)

    def clean_html(self, raw_html: str | Any) -> str:
        raw_html = str(raw_html)
        return bleach.clean(
            raw_html,
            tags=self.ALLOWED_TAGS,
            attributes=self.ALLOWED_ATTRIBUTES,
            css_sanitizer=self.css_sanitizer,
            strip=True,  # Remove disallowed tags entirely
        )

    def display_text_as_html(self, text: str | Any) -> str:
        html_text = text.replace("\n", "<br>")
        return html_text
