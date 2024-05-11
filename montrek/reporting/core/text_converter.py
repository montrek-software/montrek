import re


class HtmlLatexConverter:
    @staticmethod
    def convert(text: str) -> str:
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
        return text

    @staticmethod
    def bold(text: str) -> str:
        return text.replace("<b>", "\\textbf{").replace("</b>", "}")

    @staticmethod
    def italic(text: str) -> str:
        return text.replace("<i>", "\\textit{").replace("</i>", "}")

    @staticmethod
    def headers(text: str) -> str:
        patterns = {
            "<h1>": "\\section{",
            "</h1>": "}",
            "<h2>": "\\subsection{",
            "</h2>": "}",
            "<h3>": "\\large{\\textbf{",
            "</h3>": "}}",
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
    def lists(text: str) -> str:
        # Convert lists
        text = re.sub(
            r"<ul>(.*?)</ul>",
            r"\\begin{itemize} \1 \\end{itemize}",
            text,
            flags=re.DOTALL,
        )
        text = re.sub(
            r"<ol>(.*?)</ol>",
            r"\\begin{enumerate} \1 \\end{enumerate}",
            text,
            flags=re.DOTALL,
        )
        text = re.sub(r"<li>(.*?)</li>", r"\\item \1", text)
        return text
