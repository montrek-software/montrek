from django.forms import Form


class MontrekReportForm(Form): ...


class NoMontrekReportForm(MontrekReportForm):
    def to_html(self) -> str:
        return ""
