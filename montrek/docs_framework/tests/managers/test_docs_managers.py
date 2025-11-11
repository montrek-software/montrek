from django.test import TestCase
from docs_framework.managers.docs_managers import DocsManager
from docs_framework.mixins.docs_mixins import DocsFilesMixin


class TestDocsManager(TestCase, DocsFilesMixin):
    def setUp(self):
        docs_file = self.get_docs_file_by_name("docs_1")
        self.manager = DocsManager({"docs_file_path": docs_file.docs_path})

    def test_convert_md_to_html(self):
        test_html = self.manager.to_html()
        expected_html = """<h1>This is a Header</h1>
<h2>And a Subheader</h2>
<p>And some text</p>
<table>
<thead>
<tr>
<th>Maybe a</th>
<th>little</th>
</tr>
</thead>
<tbody>
<tr>
<td>or</td>
<td>so...</td>
</tr>
<tr>
<td>and</td>
<td>on</td>
</tr>
</tbody>
</table><div style="height:2cm"></div><hr><div style="color:grey">Internal Report</div>"""
        self.assertEqual(test_html, expected_html)
