from django.test import TestCase
from reporting.core.text_converter import HtmlLatexConverter


class TestHtmlLatexConverter(TestCase):
    def test_html_to_latex(self):
        test_text = (
            "This is a <b>html</b> text. <br> This is a new <i>line</i> and a &middot;"
        )
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "This is a \\textbf{html} text. \\newline  This is a new \\textit{line} and a $\\cdot$"
        self.assertEqual(converted_text, expected_text)

    def test_ignored(self):
        test_text = "<html><body><div class='col-md-6'><div class='col-md-6'>Text</div></div></body></html>"
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "Text"
        self.assertEqual(converted_text, expected_text)

    def test_headers(self):
        test_text = "<h1>Header 1</h1><h2>Header 2</h2>"
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "\\section*{Header 1}\\subsection*{Header 2}"
        self.assertEqual(converted_text, expected_text)

    def test_links(self):
        test_text = '<a href="http://example.com">Example</a>'
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "\\textcolor{blue}{\\href{http://example.com}{Example}}"
        self.assertEqual(converted_text, expected_text)

    def test_images(self):
        test_text = '<img src="image.png">'
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "\\includegraphics{image.png}"
        self.assertEqual(converted_text, expected_text)

    def test_lists(self):
        test_text = "<ul><li>Item 1</li><li>Item 2</li></ul><ol><li>First</li><li>Second</li></ol>"
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "\\begin{itemize} \\item Item 1\\item Item 2 \\end{itemize}\\begin{enumerate} \\item First\\item Second \\end{enumerate}"
        self.assertEqual(converted_text, expected_text)

    def test_lists_nested(self):
        test_text = "<ul><li>Item 1</li><li>Item 2<ul><li>Subitem 2.1</li><li>Subitem 2.2</li></ul></li></ul>"
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "\\begin{itemize} \\item Item 1\\item Item 2\\begin{itemize} \\item Subitem 2.1\\item Subitem 2.2 \\end{itemize} \\end{itemize}"
        self.assertEqual(converted_text, expected_text)

    def test_tables(self):
        test_text = "<table><tr><td>Cell 1</td><td>Cell 2</td></tr></table>"
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "\\begin{tabular}{|c|} \\hline Cell 1 & Cell 2 &  \\\\ \\hline \\end{tabular} "
        self.assertEqual(converted_text, expected_text)

    def test_special_characters(self):
        test_text = "Special characters: &lt;, &gt;, &amp;"
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "Special characters: $<$, $>$, \\&"
        self.assertEqual(converted_text, expected_text)

    def test_sub_sup_script(self):
        test_text = "H<sub>2</sub>O and E = mc<sup>2</sup>"
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "H$_{2}$O and E = mc$^{2}$"
        self.assertEqual(converted_text, expected_text)

    def test_text_alignment(self):
        test_text = '<div style="text-align: center">Centered Text</div>'
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "\\begin{center} Centered Text \\end{center}"
        self.assertEqual(converted_text, expected_text)
