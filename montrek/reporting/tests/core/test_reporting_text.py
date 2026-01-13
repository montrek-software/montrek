import os
from bs4 import BeautifulSoup
import tempfile
from dataclasses import dataclass
from unittest.mock import Mock, patch

from django.test import TestCase
from reporting.core.reporting_text import (
    MarkdownReportingElement,
    MontrekLogo,
    NewPage,
    ReportingBold,
    ReportingEditableText,
    ReportingElement,
    ReportingHeader1,
    ReportingHeader2,
    ReportingImage,
    ReportingItalic,
    ReportingMap,
    ReportingParagraph,
    ReportingText,
    ReportingFooter,
    ReportingTextParagraph,
    Vspace,
    ReportingError,
)


@dataclass
class MockObject:
    field: str


@dataclass
class MockIntObject:
    field: int


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
        self.assertEqual(
            self.reporting_element.to_html().replace("\n", "").replace(" ", ""),
            self.expected_html.replace("\n", "").replace(" ", ""),
        )

    def test_to_latex(self):
        if self.__class__.__name__ == "ReportingElementTestCase":
            return
        self.assertEqual(self.reporting_element.to_latex(), self.expected_latex)

    def test_to_json(self):
        if self.__class__.__name__ == "ReportingElementTestCase":
            return
        self.assertEqual(self.reporting_element.to_json(), self.expected_json)


class DummyReportingElement(ReportingElement):
    template_name = "test"


class TestReportingElementGeneral(TestCase):
    def test_to_latex(self):
        reporting_element = DummyReportingElement()
        latex = reporting_element.to_latex()
        # Headers
        self.assertIn(r"\section*{Header One}", latex)
        self.assertIn(r"\subsection*{Header Two}", latex)
        self.assertIn(r"\textbf{Header Three}\\", latex)
        self.assertIn(r"\paragraph{Header Four}", latex)
        self.assertIn(r"\subparagraph{Header Five}", latex)

        # Paragraphs
        self.assertIn(r"\begin{justify}", latex)
        self.assertIn(r"\end{justify}", latex)

        # Bold / Italic
        self.assertIn(r"\textbf{bold}", latex)
        self.assertIn(r"\textit{italic}", latex)

        # Special characters
        self.assertIn(r"\#", latex)
        self.assertIn(r"\_", latex)
        self.assertIn(r"\%", latex)
        self.assertIn(r"\&", latex)
        self.assertIn(r"$<$", latex)
        self.assertIn(r"$>$", latex)
        self.assertIn(r"$\cdot$", latex)

        # Sub / Sup
        self.assertIn(r"$_{1}$", latex)
        self.assertIn(r"$^{2}$", latex)

        # Line break
        self.assertIn(r"\newline", latex)

        # Lists
        self.assertIn(r"\begin{itemize}", latex)
        self.assertIn(r"\item Item A", latex)
        self.assertIn(r"\end{itemize}", latex)

        self.assertIn(r"\begin{enumerate}", latex)
        self.assertIn(r"\item First", latex)
        self.assertIn(r"\end{enumerate}", latex)

        # Links
        self.assertIn(
            r"\textcolor{blue}{\href{https://example.com}{Example}}",
            latex,
        )

        # Images
        self.assertIn(r"\includegraphics{image.png}", latex)

        # Alignment
        self.assertIn(r"\begin{center} Centered \end{center}", latex)

        # Emojis
        self.assertIn(r"\twemoji{rocket}", latex)
        self.assertIn(r"\twemoji{pencil}", latex)
        self.assertIn(r"\twemoji{wastebasket}", latex)

        # Ignored wrapper div
        self.assertNotIn("col-md-6", latex)

        # Table
        self.assertIn(r"\begin{tabular}{|l|l|}", latex)
        self.assertIn(r"\hline", latex)
        self.assertIn(r"Name \& Age \\", latex)
        self.assertIn(r"Alice \& 30 \\", latex)
        self.assertIn(r"\end{tabular}", latex)


class TestReportingText(ReportingElementTestCase):
    reporting_element_class = ReportingText
    expected_html = "Dummy Text"
    expected_latex = "Dummy Text"
    expected_json = {"reportingtext": "Dummy Text"}

    def get_call_parameters(self) -> dict:
        return {"text": "Dummy Text"}


class TestReportingBold(ReportingElementTestCase):
    reporting_element_class = ReportingBold
    expected_html = "<strong>Dummy Text</strong>"
    expected_latex = "\\textbf{Dummy Text}"
    expected_json = {"reportingbold": "Dummy Text"}

    def get_call_parameters(self) -> dict:
        return {"text": "Dummy Text"}


class TestReportingItalic(ReportingElementTestCase):
    reporting_element_class = ReportingItalic
    expected_html = "<em>Dummy Text</em>"
    expected_latex = "\\emph{Dummy Text}"
    expected_json = {"reportingitalic": "Dummy Text"}

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
    expected_html = '<div style="page-break-after: always; height:15mm;"><hr></div>'
    expected_latex = "\\newpage"
    expected_json = {"new_page": True}


class TestReportingImage(ReportingElementTestCase):
    reporting_element_class = ReportingImage
    expected_html = '<div style="text-align: right;"><img src="https://example.com/properties/lakeside_residences.jpg" alt="image" width="100.0%" height="auto"></div>'
    expected_latex = (
        "Image not found: https://example.com/properties/lakeside\\_residences.jpg"
    )
    expected_json = {
        "reporting_image": "https://example.com/properties/lakeside_residences.jpg"
    }

    def get_call_parameters(self) -> dict:
        return {"image_path": "https://example.com/properties/lakeside_residences.jpg"}

    def test_urllike_but_no_html(self):
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"\x89PNG\r\n\x1a\n")  # Write minimal PNG header
            tmp_path = tmp.name

        try:
            reporting_image = ReportingImage(tmp_path)
            latex_path = reporting_image.to_latex()
            cleaned_tmp_path = tmp_path.replace("_", r"\_")
            expected = rf"\includegraphics[width=1.0\textwidth]{{{cleaned_tmp_path}}}"
            self.assertEqual(latex_path, expected)
        finally:
            os.remove(tmp_path)  # Clean up the temporary file

    def test_image_not_found(self):
        image_path = "abcd.png"
        reporting_image = ReportingImage(image_path)
        latex_path = reporting_image.to_latex()
        self.assertEqual(latex_path, "")

    @patch("reporting.core.reporting_text.requests.get")
    def test_to_latex(self, mock_get):
        mock_get.return_value = Mock(status_code=401, content=b"\x89PNG\r\n\x1a\n...")
        super().test_to_latex()
        mock_get.assert_called_once_with(
            "https://example.com/properties/lakeside_residences.jpg", timeout=5
        )


class TestReportingMap(ReportingElementTestCase):
    reporting_element_class = ReportingMap
    expected_html = '<iframe src="https://www.openstreetmap.org/export/embed.html?bbox=5%2C15%2C15%2C25&amp;layer=mapnik&amp;marker=20%2C10" style="width: 100%; aspect-ratio: 4/3; height: auto; border:2;" loading="lazy" allowfullscreen></iframe>'
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
    expected_html = '<div class="row">\n         <div class="col"><h2></h2></div>\n         <div id="field-content-container-field">\n             <div class="row border p-3 mx-1">\n    <div class="col scrollable-600">field_content<br></div>\n  </div>\n  <div class="row p-2">\n    <div class="col-lg-1">\n      <button\n        class="btn btn-custom"\n        hx-get="dummy?mode=edit&field=field"\n        hx-target="#field-content-container-field"\n      >\n        <span class="bi bi-pencil" />\n      </button>\n    </div>\n    <div class="col-lg-11"></div>\n  </div>\n</div>\n\n         </div>'
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
        cls.plain_html_text = '<div class="scrollable-600">This is a plain text</div>'
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

    def test_paragraph_plain(self):
        paragraph = ReportingTextParagraph(self.plain_text)
        self.assertEqual(paragraph.text, self.plain_text)
        self.assertEqual(paragraph.text_type.name, "PLAIN")
        test_plain_to_html = paragraph.format_html()
        self.assertEqual(test_plain_to_html, self.plain_html_text)
        test_plain_to_latex = paragraph.format_latex()
        self.assertEqual(test_plain_to_latex, self.plain_latex_text)

    def test_reporting_editable_text(self):
        mock_object = MockObject(field="AA123")
        element = ReportingEditableText(
            obj=mock_object, field="field", edit_url="test_url"
        )

        self.assertEqual(element.text, "AA123")

        soup = BeautifulSoup(element.to_html(), "html.parser")

        # Root row
        root = soup.find("div", class_="row")
        self.assertIsNotNone(root)

        # Header
        h2 = root.find("h2")
        self.assertIsNotNone(h2)
        self.assertEqual(h2.get_text(strip=True), "")

        # Content container
        container = soup.find(id="field-content-container-field")
        self.assertIsNotNone(container)

        # Rendered text with <br>
        content_col = container.find("div", class_="scrollable-600")
        self.assertIsNotNone(content_col)
        self.assertIn("AA123", content_col.get_text())
        self.assertIsNotNone(content_col.find("br"))

        # Edit button
        button = soup.find("button", attrs={"hx-get": True})
        self.assertIsNotNone(button)
        self.assertEqual(
            button["hx-get"],
            "test_url?mode=edit&field=field",
        )
        self.assertEqual(
            button["hx-target"],
            "#field-content-container-field",
        )

    def test_reporting_editable_text__no_string(self):
        mock_object = MockIntObject(field=123)
        element = ReportingEditableText(
            obj=mock_object, field="field", edit_url="test_url"
        )

        self.assertEqual(element.text, "123")

        soup = BeautifulSoup(element.to_html(), "html.parser")

        # Root row
        root = soup.find("div", class_="row")
        self.assertIsNotNone(root)

        # Header
        h2 = root.find("h2")
        self.assertIsNotNone(h2)
        self.assertEqual(h2.get_text(strip=True), "")

        # Content container
        container = soup.find(id="field-content-container-field")
        self.assertIsNotNone(container)

        # Rendered text with <br>
        content_col = container.find("div", class_="scrollable-600")
        self.assertIsNotNone(content_col)
        self.assertIn("123", content_col.get_text())
        self.assertIsNotNone(content_col.find("br"))

        # Edit button
        button = soup.find("button", attrs={"hx-get": True})
        self.assertIsNotNone(button)
        self.assertEqual(
            button["hx-get"],
            "test_url?mode=edit&field=field",
        )
        self.assertEqual(
            button["hx-target"],
            "#field-content-container-field",
        )

    def test_reporting_editable_text_display_newline(self):
        mock_object = MockObject(field="AA123\nNewline")
        element = ReportingEditableText(
            obj=mock_object, field="field", edit_url="test_url"
        )

        self.assertEqual(element.text, "AA123\nNewline")

        soup = BeautifulSoup(element.to_html(), "html.parser")

        content_col = soup.find("div", class_="scrollable-600")
        self.assertIsNotNone(content_col)

        # Text split by <br>
        parts = list(content_col.stripped_strings)
        self.assertEqual(parts, ["AA123", "Newline"])

        # Explicitly assert line break exists
        self.assertTrue(content_col.find("br"))

    def test_reporting_editable_text_with_header(self):
        mock_object = MockObject(field="AA123")
        element = ReportingEditableText(
            obj=mock_object,
            field="field",
            edit_url="test_url",
            header="Test Header",
        )

        self.assertEqual(element.text, "AA123")

        soup = BeautifulSoup(element.to_html(), "html.parser")

        # Header
        h2 = soup.find("h2")
        self.assertIsNotNone(h2)
        self.assertEqual(h2.get_text(strip=True), "Test Header")

        # Content still correct
        content_col = soup.find("div", class_="scrollable-600")
        self.assertIsNotNone(content_col)
        self.assertIn("AA123", content_col.get_text())

        # Button wiring still correct
        button = soup.find("button", attrs={"hx-get": True})
        self.assertEqual(
            button["hx-get"],
            "test_url?mode=edit&field=field",
        )

    def test_reporting_text_with_none(self):
        reporting_text = ReportingText(None)
        self.assertEqual(reporting_text.to_html(), "\n")
        self.assertEqual(reporting_text.to_latex(), "")


class TestReportingParagraph(TestCase):
    def test_plain_text(self):
        paragraph = ReportingParagraph("This is a plain text")
        self.assertEqual(paragraph.text, "This is a plain text")
        self.assertEqual(paragraph.reporting_text_type.name, "HTML")
        test_plain_to_html = paragraph.to_html()
        self.assertEqual(
            test_plain_to_html.replace("\n", ""), "<p>This is a plain text</p>"
        )
        test_plain_to_latex = paragraph.to_latex()
        self.assertEqual(
            test_plain_to_latex,
            "\\begin{justify}This is a plain text\\end{justify}",
        )

    def test_bold_text(self):
        paragraph = MarkdownReportingElement("This is a **bold** text")
        self.assertEqual(paragraph.markdown_text, "This is a **bold** text")
        test_bold_to_html = paragraph.to_html()
        self.assertEqual(
            test_bold_to_html, "<p>This is a <strong>bold</strong> text</p>\n\n"
        )
        test_bold_to_latex = paragraph.to_latex()
        self.assertEqual(
            test_bold_to_latex,
            "\\begin{contentbox}This is a \\textbf{bold} text\n\\end{contentbox}",
        )

    def test_italic_text(self):
        paragraph = MarkdownReportingElement("This is a *italic* text")
        self.assertEqual(paragraph.markdown_text, "This is a *italic* text")
        test_italic_to_html = paragraph.to_html()
        self.assertEqual(
            test_italic_to_html, "<p>This is a <em>italic</em> text</p>\n\n"
        )
        test_italic_to_latex = paragraph.to_latex()
        self.assertEqual(
            test_italic_to_latex,
            "\\begin{contentbox}This is a \\emph{italic} text\n\\end{contentbox}",
        )


class TestMontrekLogo(TestCase):
    def test_logo(self):
        logo = MontrekLogo(width=0.5)
        self.assertEqual(logo.width, 0.5)
        self.assertEqual(
            logo.to_html(),
            '<div style="text-align: right;"><img src="http://static1.squarespace.com/static/673bfbe149f99b59e4a41ee7/t/673bfdb41644c858ec83dc7e/1731984820187/montrek_logo_variant.png?format=1500w" alt="image" width="50.0%" height="auto"></div>\n',
        )
        logo_str = logo.to_latex()
        self.assertTrue(logo_str.startswith("\\includegraphics[width=0.5\\textwidth]{"))
        self.assertIn(
            "reporting/.workbench/b1c15ab1db73597bedf8ace0d4521004c58c0feb98858703ecc255f966c8008e.png",
            logo.to_latex(),
        )
        self.assertTrue(logo_str.endswith("}"))


class TestMarkdownReportingElement(ReportingElementTestCase):
    reporting_element_class = MarkdownReportingElement
    expected_html = (
        "<p>This is a <strong>bold</strong> text with a table:</p>\n"
        "<table>\n<thead>\n<tr>\n<th>Header1</th>\n<th>Header2</th>\n</tr>\n</thead>\n"
        "<tbody>\n<tr>\n<td>Cell1</td>\n<td>Cell2</td>\n</tr>\n</tbody>\n</table>"
    )
    expected_latex = "\\begin{contentbox}This is a \\textbf{bold} text with a table:\n\n\\begin{longtable}[]{@{}ll@{}}\n\\toprule\\noalign{}\nHeader1 & Header2 \\\\\n\\midrule\\noalign{}\n\\endhead\n\\bottomrule\\noalign{}\n\\endlastfoot\nCell1 & Cell2 \\\\\n\\end{longtable}\n\\end{contentbox}"
    expected_json = {
        "markdown_reporting_element": "This is a **bold** text with a table:\n\n| Header1 | Header2 |\n|---------|---------|\n| Cell1   | Cell2   |"
    }

    def get_call_parameters(self) -> dict:
        markdown_text = "This is a **bold** text with a table:\n\n| Header1 | Header2 |\n|---------|---------|\n| Cell1   | Cell2   |"
        return {"markdown_text": markdown_text}

    def test_malicious_text(self):
        text = "<script>HACKERATTACK</script>"
        rep_element = self.reporting_element_class(text)
        test_html = rep_element.to_html()
        self.assertEqual(test_html, "HACKERATTACK\n\n\n")


class TestReportingError(ReportingElementTestCase):
    reporting_element_class = ReportingError
    expected_html = '<divclass="alertalert-danger"><strong>ErrorHeader</strong></div><divclass="alertalert-danger">ErrorText1<br>ErrorText2<br></div>'
    expected_latex = r"\textbf{Error Header}\\Error Text1\\Error Text2"
    expected_json = {
        "error_header": "Error Header",
        "error_texts": ["Error Text1", "Error Text2"],
    }

    def get_call_parameters(self) -> dict:
        return {
            "error_texts": ["Error Text1", "Error Text2"],
            "error_header": "Error Header",
        }


class TestReportingFooter(ReportingElementTestCase):
    reporting_element_class = ReportingFooter
    expected_html = (
        '<divstyle="height:2cm"></div><hr><divstyle="color:grey">FooterText</div>'
    )
    expected_latex = "Footer Text"
    expected_json = {"reportingfooter": "Footer Text"}

    def get_call_parameters(self) -> dict:
        return {"text": "Footer Text"}
