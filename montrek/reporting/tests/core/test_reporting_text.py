from django.test import TestCase

from reporting.core.reporting_text import ReportingTextParagraph


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
