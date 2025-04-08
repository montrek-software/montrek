from dataclasses import dataclass
from django.test import TestCase

from reporting.core.reporting_text import (
    MarkdownReportElement,
    ReportingParagraph,
    ReportingText,
    ReportingTextParagraph,
    MontrekLogo,
    ReportingEditableText,
)
from reporting.constants import ReportingTextType


@dataclass
class MockObject:
    field: str


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
        mock_object = MockObject(field="AA123")
        test_element = ReportingEditableText(
            obj=mock_object, field="field", edit_url="test_url"
        )
        self.assertEqual(test_element.text, "AA123")
        self.assertEqual(
            test_element.to_html(),
            """<div class="container-fluid">
        <div class="row">
         <div class="col-lg-12" style="padding:0"><h2></h2></div>
         <div id="field-content-container-field">
             <div class="container-fluid p-0">
  <div class="row border p-3">
    <div class="col">AA123</div>
  </div>
  <div class="row p-2">
    <div class="col-lg-1">
      <button
        class="btn btn-primary"
        hx-get="test_url?mode=edit&field=field"
        hx-target="#field-content-container-field"
      >
        <span class="glyphicon glyphicon-pencil" />
      </button>
    </div>
    <div class="col-lg-11"></div>
  </div>
</div>

         </div>
        </div>
</div>""",
        )

    def test_reporting_editable_text_with_header(self):
        mock_object = MockObject(field="AA123")
        test_element = ReportingEditableText(
            obj=mock_object, field="field", edit_url="test_url", header="Test Header"
        )
        self.assertEqual(test_element.text, "AA123")
        self.assertEqual(
            test_element.to_html(),
            """<div class="container-fluid">
        <div class="row">
         <div class="col-lg-12" style="padding:0"><h2>Test Header</h2></div>
         <div id="field-content-container-field">
             <div class="container-fluid p-0">
  <div class="row border p-3">
    <div class="col">AA123</div>
  </div>
  <div class="row p-2">
    <div class="col-lg-1">
      <button
        class="btn btn-primary"
        hx-get="test_url?mode=edit&field=field"
        hx-target="#field-content-container-field"
      >
        <span class="glyphicon glyphicon-pencil" />
      </button>
    </div>
    <div class="col-lg-11"></div>
  </div>
</div>

         </div>
        </div>
</div>""",
        )

    def test_reporting_text_with_none(self):
        reporting_text = ReportingText(None)
        self.assertEqual(reporting_text.to_html(), "")
        self.assertEqual(reporting_text.to_latex(), "")


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
        self.assertRegex(
            logo.to_latex(),
            r"\\includegraphics\[width=0.5\\textwidth\]\{/tmp/tmp[a-zA-Z0-9_]+\.png\}",
        )


class TestMarkdownReportElement(TestCase):
    def test_markdown_to_html(self):
        markdown_text = "This is a **bold** text with a table:\n\n| Header1 | Header2 |\n|---------|---------|\n| Cell1   | Cell2   |"
        element = MarkdownReportElement(markdown_text)
        expected_html = (
            "<p>This is a <strong>bold</strong> text with a table:</p>\n"
            "<table>\n<thead>\n<tr>\n<th>Header1</th>\n<th>Header2</th>\n</tr>\n</thead>\n"
            "<tbody>\n<tr>\n<td>Cell1</td>\n<td>Cell2</td>\n</tr>\n</tbody>\n</table>"
        )
        self.assertEqual(element.to_html(), expected_html)

    def test_markdown_to_latex(self):
        markdown_text = "This is a **bold** text with a table:\n\n| Header1 | Header2 |\n|---------|---------|\n| Cell1   | Cell2   |"
        element = MarkdownReportElement(markdown_text)
        latex_output = element.to_latex()
        self.assertIn("\\textbf{bold}", latex_output)
        self.assertIn("\\begin{tabular}", latex_output)
        self.assertIn("Header1 & Header2 \\\\", latex_output)
        self.assertIn("Cell1 & Cell2 \\\\", latex_output)
