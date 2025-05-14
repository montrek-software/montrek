from dataclasses import dataclass
from django.test import TestCase

from reporting.core.reporting_text import (
    MarkdownReportingElement,
    NewPage,
    ReportingImage,
    ReportingMap,
    ReportingParagraph,
    ReportingText,
    ReportingTextParagraph,
    MontrekLogo,
    ReportingEditableText,
    ReportingHeader1,
    ReportingHeader2,
    Vspace,
)
from reporting.constants import ReportingTextType


@dataclass
class MockObject:
    field: str


class ReportingElementTestCase(TestCase):
    reporting_element_class = None
    expected_html = ""
    expected_latex = ""
    expected_json = {}

    def get_call_parameters(self) -> dict:
        return {}

    def setUp(self) -> None:
        if self.__class__.__name__ == "ReportingElementTestCase":
            return
        self.reporting_element = self.reporting_element_class(
            **self.get_call_parameters()
        )

    def test_to_html(self):
        if self.__class__.__name__ == "ReportingElementTestCase":
            return
        self.assertEqual(self.reporting_element.to_html(), self.expected_html)

    def test_to_latex(self):
        if self.__class__.__name__ == "ReportingElementTestCase":
            return
        self.assertEqual(self.reporting_element.to_latex(), self.expected_latex)

    def test_to_json(self):
        if self.__class__.__name__ == "ReportingElementTestCase":
            return
        self.assertEqual(self.reporting_element.to_json(), self.expected_json)


class TestReportingText(ReportingElementTestCase):
    reporting_element_class = ReportingText
    expected_html = "Dummy Text"
    expected_latex = "Dummy Text"
    expected_json = {"reportingtext": "Dummy Text"}

    def get_call_parameters(self) -> dict:
        return {"text": "Dummy Text"}


class TestReportingHeader1(ReportingElementTestCase):
    reporting_element_class = ReportingHeader1
    expected_html = "<h1>Dummy Text</h1>"
    expected_latex = "\\section*{Dummy Text}"
    expected_json = {"reporting_header_1": "Dummy Text"}

    def get_call_parameters(self) -> dict:
        return {"text": "Dummy Text"}


class TestReportingHeader2(ReportingElementTestCase):
    reporting_element_class = ReportingHeader2
    expected_html = "<h2>Dummy Text</h2>"
    expected_latex = "\\subsection*{Dummy Text}"
    expected_json = {"reporting_header_2": "Dummy Text"}

    def get_call_parameters(self) -> dict:
        return {"text": "Dummy Text"}


class TestVspace(ReportingElementTestCase):
    reporting_element_class = Vspace
    expected_html = '<div style="height:3mm;"></div>'
    expected_latex = "\\vspace{3mm}"
    expected_json = {"vspace": 3}

    def get_call_parameters(self) -> dict:
        return {"space": 3}


class TestNewPage(ReportingElementTestCase):
    reporting_element_class = NewPage
    expected_html = "<div style='page-break-after: always; height:15mm;'><hr></div>"
    expected_latex = "\\newpage"
    expected_json = {"new_page": True}


class TestReportingImage(ReportingElementTestCase):
    reporting_element_class = ReportingImage
    expected_html = '<div style="text-align: right;"><img src="https://example.com/properties/lakeside_residences.jpg" alt="image" style="width:100.0%;"></div>'
    expected_latex = (
        "Image not found: https://example.com/properties/lakeside\\_residences.jpg"
    )
    expected_json = {
        "reporting_image": "https://example.com/properties/lakeside_residences.jpg"
    }

    def get_call_parameters(self) -> dict:
        return {"image_path": "https://example.com/properties/lakeside_residences.jpg"}


class TestReportingMap(ReportingElementTestCase):
    reporting_element_class = ReportingMap
    expected_html = '<iframe src="https://www.openstreetmap.org/export/embed.html?bbox=5%2C15%2C15%2C25&layer=mapnik&marker=20%2C10" style="width: 100%; aspect-ratio: 4/3; height: auto; border:2;" loading="lazy" allowfullscreen></iframe>'
    expected_latex = ""
    expected_json = {
        "reporting_map": "https://www.openstreetmap.org/export/embed.html?bbox=5%2C15%2C15%2C25&layer=mapnik&marker=20%2C10"
    }

    def get_call_parameters(self) -> dict:
        return {"longitude": 10, "latitude": 20}


class TestReportingParagraphSmoke(ReportingElementTestCase):
    reporting_element_class = ReportingParagraph
    expected_html = "<p>Dummy Text</p>"
    expected_latex = "\\begin{justify}Dummy Text\\end{justify}"
    expected_json = {"reportingparagraph": "Dummy Text"}

    def get_call_parameters(self) -> dict:
        return {"text": "Dummy Text"}


class TestReportingEditableTextSmoke(ReportingElementTestCase):
    reporting_element_class = ReportingEditableText
    expected_html = '<div class="container-fluid">\n        <div class="row">\n         <div class="col-lg-12" style="padding:0"><h2></h2></div>\n         <div id="field-content-container-field">\n             <div class="container-fluid p-0">\n  <div class="row border p-3">\n    <div class="col">field_content</div>\n  </div>\n  <div class="row p-2">\n    <div class="col-lg-1">\n      <button\n        class="btn btn-primary"\n        hx-get="dummy?mode=edit&field=field"\n        hx-target="#field-content-container-field"\n      >\n        <span class="glyphicon glyphicon-pencil" />\n      </button>\n    </div>\n    <div class="col-lg-11"></div>\n  </div>\n</div>\n\n         </div>\n        </div>\n</div>'
    expected_latex = "\\begin{justify}field\\_content\\end{justify}"
    expected_json = {"reportingeditabletext": "field_content"}

    def get_call_parameters(self) -> dict:
        return {
            "obj": MockObject("field_content"),
            "field": "field",
            "edit_url": "dummy",
        }


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
            r"\\includegraphics\[width=0.5\\textwidth\]\{/tmp/tmp[a-zA-Z0-9\\_]+\.png\}",
        )


class TestMarkdownReportingElement(ReportingElementTestCase):
    reporting_element_class = MarkdownReportingElement
    expected_html = (
        "<p>This is a <strong>bold</strong> text with a table:</p>\n"
        "<table>\n<thead>\n<tr>\n<th>Header1</th>\n<th>Header2</th>\n</tr>\n</thead>\n"
        "<tbody>\n<tr>\n<td>Cell1</td>\n<td>Cell2</td>\n</tr>\n</tbody>\n</table>"
    )
    expected_latex = "\\begin{justify}This is a \\textbf{bold} text with a table:\\end{justify}\n\n\n<table>\n<thead>\n<tr>\n<th>Header1</th>\n<th>Header2</th>\n</tr>\n</thead>\n<tbody>\n<tr>\n<td>Cell1</td>\n<td>Cell2</td>\n</tr>\n</tbody>\n</table>"
    expected_json = {
        "markdown_reporting_element": "This is a **bold** text with a table:\n\n| Header1 | Header2 |\n|---------|---------|\n| Cell1   | Cell2   |"
    }

    def get_call_parameters(self) -> dict:
        markdown_text = "This is a **bold** text with a table:\n\n| Header1 | Header2 |\n|---------|---------|\n| Cell1   | Cell2   |"
        return {"markdown_text": markdown_text}
