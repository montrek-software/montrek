from django.test import SimpleTestCase
from reporting.modules.markdown_table import MarkdownTable


class TestMarkdownTable(SimpleTestCase):
    def test_table_with_headers(self):
        markdown = MarkdownTable(
            rows=[["a", "1"], ["b", "2"]],
            headers=["Name", "Count"],
            right_aligned=frozenset({1}),
        ).to_markdown()
        self.assertEqual(
            markdown,
            "| Name | Count |\n| --- | ---: |\n| a | 1 |\n| b | 2 |\n",
        )

    def test_empty_header_row_without_headers(self):
        markdown = MarkdownTable(rows=[["Label", "Value"]]).to_markdown()
        self.assertEqual(markdown, "|  |  |\n| --- | --- |\n| Label | Value |\n")

    def test_short_rows_are_padded(self):
        markdown = MarkdownTable(rows=[["a"]], headers=["A", "B"]).to_markdown()
        self.assertTrue(markdown.endswith("| a |  |\n"))

    def test_cells_stay_in_their_column_and_row(self):
        markdown = MarkdownTable(
            rows=[["a | b", "line 1\nline 2"]], headers=["A|B", "C"]
        ).to_markdown()
        self.assertIn("| A\\|B | C |", markdown)
        self.assertIn("| a \\| b | line 1<br>line 2 |", markdown)

    def test_no_columns(self):
        self.assertEqual(MarkdownTable(rows=[]).to_markdown(), "")
