import traceback
from collections.abc import Iterable

from baseclasses.managers.montrek_manager import MontrekManager
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from mailing.repositories.mailing_repository import MailingRepository
from reporting.core import reporting_text as rt
from reporting.lib.protocols import ReportElementProtocol


class MontrekReportManager(MontrekManager):
    document_name = "document"
    document_title = "Montrek Report"
    send_mail_url = "send_mail"
    draft = False

    def __init__(self, session_data: dict[str, str], **kwargs) -> None:
        super().__init__(session_data=session_data, **kwargs)
        self._report_elements = []

    @property
    def footer_text(self) -> ReportElementProtocol:
        return rt.ReportingText("Internal Report")

    @property
    def report_elements(self) -> list[ReportElementProtocol, ...]:
        return self._report_elements

    def append_report_element(
        self, report_element: ReportElementProtocol | list[ReportElementProtocol]
    ) -> None:
        if isinstance(report_element, Iterable):
            self._report_elements.extend(report_element)
        else:
            self._report_elements.append(report_element)

    def collect_report_elements(self) -> None:
        raise NotImplementedError("This method must be implemented in the child class")

    def cleanup_report_elements(self) -> None:
        self._report_elements = []

    def to_html(self) -> str:
        html_str = ""
        try:
            self.collect_report_elements()
        except Exception as e:
            self.cleanup_report_elements()
            error_html = f'<div class="alert alert-danger"><strong>Error during report generation: {e}</strong></div>'
            if settings.DEBUG:
                error_details = traceback.format_exc()
                error_details = error_details.replace("\n", "<br>")
                error_html += f'<div class="alert">{error_details}</div>'
            else:
                error_html += (
                    '<div class="alert"> Contact admin and check Debug mode</div>'
                )
            return error_html
        for report_element in self.report_elements:
            html_str += report_element.to_html()
        html_str += self._get_footer()
        self.cleanup_report_elements()
        return html_str

    def to_latex(self) -> str:
        latex_str = ""
        self.collect_report_elements()
        for report_element in self.report_elements:
            latex_str += report_element.to_latex()
        self.cleanup_report_elements()
        return latex_str

    def to_json(self) -> list[dict]:
        self.collect_report_elements()
        return [report_element.to_json() for report_element in self.report_elements]

    def _get_footer(self) -> str:
        footer = f'<div style="height:2cm"></div><hr><div style="color:grey">{self.footer_text.to_html()}</div>'
        return footer

    def get_mail_message(self) -> str:
        return f"<div>Please find attached the report</div><div>{self.to_html()}</div>"

    def get_mail_recipients(self) -> str:
        return settings.ADMIN_MAILING_LIST

    def get_mail_kwargs(self) -> dict:
        return {}

    def prepare_mail(self, report_path) -> HttpResponseRedirect:
        mailing_repository = MailingRepository(self.session_data)
        new_mail = mailing_repository.create_by_dict(
            {
                "mail_subject": self.document_title,
                "mail_message": self.get_mail_message(),
                "mail_recipients": self.get_mail_recipients(),
                "mail_attachments": report_path,
                "mail_bcc": settings.ADMIN_MAILING_LIST,
            }
        )
        url_kwargs = {"pk": new_mail.pk}
        url_kwargs.update(self.get_mail_kwargs())
        return HttpResponseRedirect(reverse(self.send_mail_url, kwargs=url_kwargs))
