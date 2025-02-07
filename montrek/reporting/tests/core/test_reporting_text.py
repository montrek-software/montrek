from django.test import TestCase

from reporting.core.reporting_text import (
    ReportingParagraph,
    ReportingTextParagraph,
    MontrekLogo,
    ReportingEditableText,
)
from reporting.constants import ReportingTextType


class TestReportText(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.plain_text = "This is a plain text"
        cls.plain_html_text = "<p>This is a plain text</p>"
        cls.plain_latex_text = "This is a plain text\n\n"
        cls.html_text = "This is a <b>html</b> text. <br> This is a new <i>line</i>"
        cls.markdown_text = "This is a **markdown** text. \n This is a new *line*"
        cls.markdown_html_text = (
            "This is a <b>markdown</b> text. <br> This is a new <i>line</i>"
        )
        cls.markdown_latex_text = "This is a $markdown$ text. \n This is a new $line$"

        cls.latex_text = "This is a $latex$ text. \n This is a new $line$"
        cls.latex_html_text = (
            "This is a <b>latex</b> text. <br> This is a new <i>line</i>"
        )

    def test_paragraph_not_generated(self):
        paragraph = ReportingTextParagraph()
        self.assertEqual(paragraph.text, None)
        self.assertEqual(paragraph.text_type.name, "PLAIN")
        with self.assertRaises(ValueError):
            paragraph.format_html()
        with self.assertRaises(ValueError):
            paragraph.format_latex()
        with self.assertRaises(ValueError):
            paragraph.format_mail()

    def test_paragraph_plain(self):
        paragraph = ReportingTextParagraph()
        paragraph.generate(self.plain_text)
        self.assertEqual(paragraph.text, self.plain_text)
        self.assertEqual(paragraph.text_type.name, "PLAIN")
        test_plain_to_html = paragraph.format_html()
        self.assertEqual(test_plain_to_html, self.plain_html_text)
        test_plain_to_latex = paragraph.format_latex()
        self.assertEqual(test_plain_to_latex, self.plain_latex_text)

    def test_reporting_editable_text(self):
        test_element = ReportingEditableText("This is a plain text")
        self.assertEqual(test_element.text, "This is a plain text")
        self.assertEqual(
            test_element.to_html(),
            """<div class="container-fluid">
        <div class="row">
        <div class="col-lg-12" style="padding:0">This is a plain text</div>
        </div>
        <div class="row">
        <div class="col-lg-11"></div>
        <div class="col-lg-1"></div>
        </div>
</div>""",
        )

    def test_reporting_editable_text_with_url(self):
        test_element = ReportingEditableText(
            "This is a plain text", edit_url="http://example.com"
        )
        self.assertEqual(test_element.text, "This is a plain text")
        self.assertEqual(
            test_element.to_html(),
            """<div class="container-fluid">
        <div class="row">
        <div class="col-lg-12" style="padding:0">This is a plain text</div>
        </div>
        <div class="row">
        <div class="col-lg-11"></div>
        <div class="col-lg-1"><a href="http://example.com" class="btn"><span class="glyphicon glyphicon-pencil"/></a></div>
        </div>
</div>""",
        )


class TestReportingParagraph(TestCase):
    def test_plain_text(self):
        paragraph = ReportingParagraph("This is a plain text")
        self.assertEqual(paragraph.text, "This is a plain text")
        self.assertEqual(paragraph.reporting_text_type.name, "HTML")
        test_plain_to_html = paragraph.to_html()
        self.assertEqual(test_plain_to_html, "<p>This is a plain text</p>")
        test_plain_to_latex = paragraph.to_latex()
        self.assertEqual(
            test_plain_to_latex,
            "\\begin{justify}This is a plain text\\end{justify}",
        )

    def test_bold_text(self):
        paragraph = ReportingParagraph(
            "This is a <b>bold</b> text", reporting_text_type=ReportingTextType.HTML
        )
        self.assertEqual(paragraph.text, "This is a <b>bold</b> text")
        self.assertEqual(paragraph.reporting_text_type.name, "HTML")
        test_bold_to_html = paragraph.to_html()
        self.assertEqual(test_bold_to_html, "<p>This is a <b>bold</b> text</p>")
        test_bold_to_latex = paragraph.to_latex()
        self.assertEqual(
            test_bold_to_latex,
            "\\begin{justify}This is a \\textbf{bold} text\\end{justify}",
        )

    def test_italic_text(self):
        paragraph = ReportingParagraph(
            "This is a <i>italic</i> text", reporting_text_type=ReportingTextType.HTML
        )
        self.assertEqual(paragraph.text, "This is a <i>italic</i> text")
        self.assertEqual(paragraph.reporting_text_type.name, "HTML")
        test_italic_to_html = paragraph.to_html()
        self.assertEqual(test_italic_to_html, "<p>This is a <i>italic</i> text</p>")
        test_italic_to_latex = paragraph.to_latex()
        self.assertEqual(
            test_italic_to_latex,
            "\\begin{justify}This is a \\textit{italic} text\\end{justify}",
        )


class TestMontrekLogo(TestCase):
    def test_logo(self):
        logo = MontrekLogo(width=0.5)
        self.assertEqual(logo.width, 0.5)
        self.assertEqual(
            logo.to_html(),
            '<div style="text-align: right;"><img src="http://static1.squarespace.com/static/673bfbe149f99b59e4a41ee7/t/673bfdb41644c858ec83dc7e/1731984820187/montrek_logo_variant.png?format=1500w" alt="image" style="width:50.0%;"></div>',
        )
        self.assertEqual(
            logo.to_latex(),
            "\\includegraphics[width=0.5\\textwidth]{http://static1.squarespace.com/static/673bfbe149f99b59e4a41ee7/t/673bfdb41644c858ec83dc7e/1731984820187/montrek_logo_variant.png?format=1500w}",
        )
