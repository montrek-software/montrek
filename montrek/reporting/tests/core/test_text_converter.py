import datetime

from django.test import TestCase
from reporting.core.text_converter import (
    HtmlLatexConverter,
    HtmlTextConverter,
    LaTeXEscaper,
)


class TestHtmlLatexConverter(TestCase):
    def test_html_to_latex(self):
        test_text = "This is a <b>html</b> text. <br> This is a new <i>line</i> and a &middot; More<strong>strong</strong> _test #and <em>emphasis</em>."
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "This is a \\textbf{html} text. \\newline  This is a new \\textit{line} and a $\\cdot$ More\\textbf{strong} \\_test \\#and \\textit{emphasis}."
        self.assertEqual(converted_text, expected_text)

    def test_ignored(self):
        test_text = '<html><body><div class="col-md-9"><div class="col-md-6">Text</div></div></body></html>'
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "Text"
        self.assertEqual(converted_text, expected_text)

    def test_table(self):
        test_text = " <table> <tr> <th>Name</th> <th>Age</th> </tr> <tr> <td>Alice</td> <td>30</td> </tr> </table> "
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = " \\begin{tabular}{|l|l|}\n\\hline\nName \\& Age \\\\\n\\hline\nAlice \\& 30 \\\\\n\\hline\n\\end{tabular} "
        self.assertEqual(converted_text, expected_text)

    def test_rule(self):
        test_text = " <hr> "
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = (
            " \n\\newline\\rule{\\linewidth}{0.4pt}\\newline\\vspace{0.5em} "
        )
        self.assertEqual(converted_text, expected_text)

    def test_headers(self):
        test_text = "<h1>Header 1</h1><h2>Header 2</h2>"
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "\\section*{Header 1}\\subsection*{Header 2}"
        self.assertEqual(converted_text, expected_text)

    def test_links(self):
        test_text = '<a href="http://example.com">Example</a>'
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "\\textcolor{primary}{\\href{http://example.com}{Example}}"
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

    def test_special_characters(self):
        test_text = "Special characters: &lt;, &gt;, &amp; & _"
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "Special characters: $<$, $>$, \\& \\& \\_"
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

    def test_convert_std_icons(self):
        test_text = (
            '<span class="bi bi-pencil"></span>\n<span class="bi bi-trash"></span>'
        )
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "\\twemoji{pencil}\n\\twemoji{wastebasket}"
        self.assertEqual(converted_text, expected_text)

    def test_convert_dates(self):
        test_text = datetime.date(2025, 10, 23)
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "2025-10-23"
        self.assertEqual(converted_text, expected_text)

    def test_convert_datetime(self):
        test_text = datetime.datetime(2025, 10, 23)
        converted_text = HtmlLatexConverter.convert(test_text)
        expected_text = "2025-10-23 00:00:00"
        self.assertEqual(converted_text, expected_text)


class TestLaTeXEscaper(TestCase):
    def test_ampersand(self):
        self.assertEqual(LaTeXEscaper.escape("Revenue & Costs"), "Revenue \\& Costs")

    def test_underscore(self):
        self.assertEqual(LaTeXEscaper.escape("field_name"), "field\\_name")

    def test_hash(self):
        self.assertEqual(LaTeXEscaper.escape("item #1"), "item \\#1")

    def test_percent(self):
        self.assertEqual(LaTeXEscaper.escape("50%"), "50\\%")

    def test_angle_brackets(self):
        self.assertEqual(LaTeXEscaper.escape("a < b > c"), "a $<$ b $>$ c")

    def test_combined(self):
        self.assertEqual(
            LaTeXEscaper.escape("Fund & Partners_A #2 (50%)"),
            "Fund \\& Partners\\_A \\#2 (50\\%)",
        )

    def test_html_entity_not_decoded(self):
        # Raw text: "&amp;" is the literal 5-char sequence, & gets escaped
        self.assertEqual(LaTeXEscaper.escape("&amp;"), "\\&amp;")

    def test_non_string_coerced(self):
        self.assertEqual(LaTeXEscaper.escape(42), "42")


class TestSoftHyphenate(TestCase):
    def test_short_word_unchanged(self):
        text = "Kostenrisiko"  # 12 chars, below threshold
        self.assertEqual(HtmlLatexConverter.soft_hyphenate(text), text)

    def test_word_at_threshold_unchanged(self):
        text = "A" * 20  # exactly threshold, not above it
        self.assertEqual(HtmlLatexConverter.soft_hyphenate(text), text)

    def test_word_one_above_threshold_broken(self):
        text = "A" * 21  # threshold + 1
        expected = "A" * 10 + "\\-" + "A" * 10 + "\\-" + "A"
        self.assertEqual(HtmlLatexConverter.soft_hyphenate(text), expected)

    def test_long_german_word(self):
        word = "Kostenüberschreitungsrisiko"  # 27 chars → 10 + 10 + 7
        result = HtmlLatexConverter.soft_hyphenate(word)
        expected = word[:10] + "\\-" + word[10:20] + "\\-" + word[20:]
        self.assertEqual(result, expected)

    def test_latex_command_not_broken(self):
        # backslash immediately before a letter sequence prevents matching
        text = "\\A" * 11  # no pure-letter run of > 20 chars without backslash prefix
        self.assertEqual(HtmlLatexConverter.soft_hyphenate(text), text)

    def test_non_letter_chars_break_run(self):
        # digit and '$' split the run so no match occurs
        text = "$<$script$>$MaliciousHack"  # "MaliciousHack" = 13 chars, no match
        self.assertEqual(HtmlLatexConverter.soft_hyphenate(text), text)


class TestHtmlTextConverter(TestCase):
    def test_special_characters__no_strings(self):
        for value in (12, False, 32.1, None, "test"):
            test_value = HtmlTextConverter.convert(value)
            self.assertEqual(value, test_value)

    def test_special_characters(self):
        test_text = "Learn HTML entities: &middot; is a middle dot &middot; &amp; stands for ampersand &amp; &lt; means less than &lt; &gt; means greater than &gt; and &lowbar; represents an underscore &lowbar;"
        test_value = HtmlTextConverter.convert(test_text)
        expected_value = "Learn HTML entities: · is a middle dot · & stands for ampersand & < means less than < > means greater than > and _ represents an underscore _"
        self.assertEqual(expected_value, test_value)
