from reporting.core.reporting_text import MarkdownReportingElement
from reporting.managers.montrek_report_manager import MontrekReportManager


class DocsManager(MontrekReportManager):
    def collect_report_elements(self):
        docs_file_path = self.session_data["docs_file_path"]
        with open(docs_file_path, "r") as f:
            markdown_text = f.read()
            self.append_report_element(MarkdownReportingElement(markdown_text))
