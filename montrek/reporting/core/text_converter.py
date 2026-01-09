import re
from html import unescape
from typing import Any


class HtmlLatexConverter:
    @staticmethod
    def convert(text: str) -> str:
        text = str(text)
        text = HtmlLatexConverter.ignored(text)
        text = HtmlLatexConverter.tables(text)
        text = HtmlLatexConverter.paragraphs(text)
        text = HtmlLatexConverter.bold(text)
        text = HtmlLatexConverter.italic(text)
        text = HtmlLatexConverter.headers(text)
        text = HtmlLatexConverter.lists(text)
        text = HtmlLatexConverter.links(text)
        text = HtmlLatexConverter.images(text)
        text = HtmlLatexConverter.alignments(text)
        text = HtmlLatexConverter.newline(text)
        text = HtmlLatexConverter.emojis(text)
        text = HtmlLatexConverter.special_characters(text)
        text = HtmlLatexConverter.sub_sup_script(text)
        return text

    @staticmethod
    def ignored(text):
        for tag in ["html", "body"]:
            text = text.replace(f"<{tag}>", "").replace(f"</{tag}>", "")
        # Using loop to catch nested tags
        pattern = r'<div class="col-md-[0-9]+">(.*?)</div>'
        while re.search(pattern, text, flags=re.DOTALL):
            text = re.sub(pattern, r"\1", text, flags=re.DOTALL)
        return text

    @staticmethod
    def tables(text: str) -> str:
        table_pattern = re.compile(
            r"<table>(.*?)</table>",
            re.DOTALL,
        )

        def replace_table(match):
            table_html = match.group(1)

            rows = re.findall(r"<tr>(.*?)</tr>", table_html, re.DOTALL)
            if not rows:
                return ""

            latex_rows = []
            col_count = None

            for row in rows:
                cells = re.findall(
                    r"<t[hd]>(.*?)</t[hd]>",
                    row,
                    re.DOTALL,
                )
                cells = [c.strip() for c in cells]

                if col_count is None:
                    col_count = len(cells)

                latex_rows.append(" & ".join(cells) + r" \\")

            alignment = "|".join(["l"] * col_count)
            alignment = f"|{alignment}|"

            body = "\n\\hline\n".join(latex_rows)

            return (
                f"\\begin{{tabular}}{{{alignment}}}\n"
                "\\hline\n"
                f"{body}\n"
                "\\hline\n"
                "\\end{tabular}"
            )

        while re.search(table_pattern, text):
            text = re.sub(table_pattern, replace_table, text, count=1)

        return text

    @staticmethod
    def paragraphs(text: str) -> str:
        return text.replace("<p>", "\\begin{justify}").replace(
            "</p>", "\\end{justify}\n\n"
        )

    @staticmethod
    def bold(text: str) -> str:
        text = text.replace("<strong>", "\\textbf{").replace("</strong>", "}")
        text = text.replace("<b>", "\\textbf{").replace("</b>", "}")
        return text

    @staticmethod
    def italic(text: str) -> str:
        text = text.replace("<em>", "\\textit{").replace("</em>", "}")
        text = text.replace("<i>", "\\textit{").replace("</i>", "}")
        return text

    @staticmethod
    def headers(text: str) -> str:
        patterns = {
            "<h1>": "\\section*{",
            "</h1>": "}",
            "<h2>": "\\subsection*{",
            "</h2>": "}",
            "<h3>": "\\textbf{",
            "</h3>": "}\\\\",
            "<h4>": "\\paragraph{",
            "</h4>": "}",
            "<h5>": "\\subparagraph{",
            "</h5>": "}",
        }
        for key, value in patterns.items():
            text = text.replace(key, value)
        return text

    @staticmethod
    def newline(text: str) -> str:
        return text.replace("<br>", "\\newline ")

    @staticmethod
    def special_characters(text: str) -> str:
        characters = {
            "#": "\\#",
            "_": "\\_",
            "·": "$\\cdot$",
            "&middot;": "$\\cdot$",
            "&amp;": "&",
            "<": "$<$",
            ">": "$>$",
            "&lt;": "$<$",
            "&gt;": "$>$",
            "%": "\\%",
            "&lowbar;": "\\_",
        }
        for key, value in characters.items():
            text = text.replace(key, value)
        text = text.replace("&", "\\&")
        return text

    @staticmethod
    def sub_sup_script(text: str) -> str:
        text = text.replace("$<$sub$>$", "$_{").replace("$<$/sub$>$", "}$")
        text = text.replace("$<$sup$>$", "$^{").replace("$<$/sup$>$", "}$")
        return text

    @staticmethod
    def links(text: str) -> str:
        # Replace hrefs with a simplified LaTeX hyperlink command

        text = re.sub(
            r'<a href="([^"]*)">([^<]*)</a>', r"\\textcolor{blue}{\\href{\1}{\2}}", text
        )
        return text

    @staticmethod
    def images(text: str) -> str:
        text = re.sub(r'<img src="([^"]+)"[^>]*>', r"\\includegraphics{\1}", text)
        return text

    @staticmethod
    def alignments(text: str) -> str:
        # This will replace div tags with alignment, can be expanded to handle more cases
        text = re.sub(
            r'<div style="text-align: ([^"]*)">([^<]*)</div>',
            r"\\begin{\1} \2 \\end{\1}",
            text,
        )
        return text

    @staticmethod
    def lists(text: str) -> str:
        patterns = {
            r"<ul>(.*?)</ul>": r"\\begin{itemize} \1 \\end{itemize}",
            r"<ol>(.*?)</ol>": r"\\begin{enumerate} \1 \\end{enumerate}",
            r"<li>(.*?)</li>": r"\\item \1",
        }
        # Using loop to catch nested tags
        for pattern, replacement in patterns.items():
            while re.search(pattern, text, flags=re.DOTALL):
                text = re.sub(pattern, replacement, text, flags=re.DOTALL)
        return text

    @staticmethod
    def emojis(text: str) -> str:
        text = text.replace("🚀", "\\twemoji{rocket}")
        text = text.replace('<span class="bi bi-pencil"></span>', "\\twemoji{pencil}")
        text = text.replace(
            '<span class="bi bi-trash"></span>', "\\twemoji{wastebasket}"
        )
        return text


class HtmlTextConverter:
    @staticmethod
    def convert(text: Any) -> Any:
        text = HtmlTextConverter.special_characters(text)
        return text

    @staticmethod
    def special_characters(text: Any) -> Any:
        if not isinstance(text, str):
            return text
        return unescape(text)
