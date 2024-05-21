import re


class HtmlLatexConverter:
    @staticmethod
    def convert(text: str) -> str:
        text = HtmlLatexConverter.ignored(text)
        text = HtmlLatexConverter.paragraphs(text)
        text = HtmlLatexConverter.bold(text)
        text = HtmlLatexConverter.italic(text)
        text = HtmlLatexConverter.headers(text)
        text = HtmlLatexConverter.lists(text)
        text = HtmlLatexConverter.links(text)
        text = HtmlLatexConverter.images(text)
        text = HtmlLatexConverter.tables(text)
        text = HtmlLatexConverter.alignments(text)
        text = HtmlLatexConverter.newline(text)
        text = HtmlLatexConverter.special_characters(text)
        text = HtmlLatexConverter.sub_sup_script(text)
        print(text)
        return text

    @staticmethod
    def ignored(text):
        for tag in ["html", "body"]:
            text = text.replace(f"<{tag}>", "").replace(f"</{tag}>", "")
        # Using loop to catch nested tags
        pattern = r'<div class="col-md-[0-9]+">(.*?)</div>'
        while re.search(pattern, text):
            text = re.sub(pattern, r"\1", text, flags=re.DOTALL)
        return text

    @staticmethod
    def paragraphs(text: str) -> str:
        return text.replace("<p>", "\\begin{justify}").replace(
            "</p>", "\\end{justify}\n\n"
        )

    @staticmethod
    def bold(text: str) -> str:
        return text.replace("<b>", "\\textbf{").replace("</b>", "}")

    @staticmethod
    def italic(text: str) -> str:
        return text.replace("<i>", "\\textit{").replace("</i>", "}")

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
            "&middot;": "$\\cdot$",
            "&amp;": "\\&",
            "&lt;": "$<$",
            "&gt;": "$>$",
            "%": "\\%",
        }
        for key, value in characters.items():
            text = text.replace(key, value)
        return text

    @staticmethod
    def sub_sup_script(text: str) -> str:
        text = text.replace("<sub>", "$_{").replace("</sub>", "}$")
        text = text.replace("<sup>", "$^{").replace("</sup>", "}$")
        return text

    @staticmethod
    def links(text: str) -> str:
        # Replace hrefs with a simplified LaTeX hyperlink command
        text = re.sub(
            r'<a href="(.*?)">(.*?)</a>', r"\\textcolor{blue}{\\href{\1}{\2}}", text
        )
        return text

    @staticmethod
    def images(text: str) -> str:
        text = re.sub(r'<img src="(.*?)"[^>]*>', r"\\includegraphics{\1}", text)
        return text

    @staticmethod
    def tables(text: str) -> str:
        # Simplified table replacement, complex tables might need more specific handling
        text = text.replace("<table>", "\\begin{tabular}{|c|} \\hline ")
        text = text.replace("</table>", "\\end{tabular} ")
        text = text.replace("<tr>", "")
        text = text.replace("</tr>", " \\\\ \\hline ")
        text = text.replace("<td>", "")
        text = text.replace("</td>", " & ")
        return text

    @staticmethod
    def alignments(text: str) -> str:
        # This will replace div tags with alignment, can be expanded to handle more cases
        text = re.sub(
            r'<div style="text-align: (.*?)">(.*?)</div>',
            r"\\begin{\1} \2 \\end{\1}",
            text,
        )
        return text

    @staticmethod
    # Using loops to catch nested tags
    def lists(text: str) -> str:
        ul_pattern = r"<ul>(.*?)</ul>"
        while re.search(ul_pattern, text):
            text = re.sub(
                ul_pattern,
                r"\\begin{itemize} \1 \\end{itemize}",
                text,
                flags=re.DOTALL,
            )
        ol_pattern = r"<ol>(.*?)</ol>"
        while re.search(ol_pattern, text):
            text = re.sub(
                ol_pattern,
                r"\\begin{enumerate} \1 \\end{enumerate}",
                text,
                flags=re.DOTALL,
            )
        li_pattern = r"<li>(.*?)</li>"
        while re.search(li_pattern, text):
            text = re.sub(li_pattern, r"\\item \1", text, flags=re.DOTALL)
        return text
