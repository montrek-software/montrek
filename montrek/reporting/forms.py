from django.forms import Form


class MontrekReportForm(Form):
    template: str | None = None

    def to_html(self) -> str:
        if not self.template:
            raise NotImplementedError("MontrekReportForm needs template attribute")
        return ""


class NoMontrekReportForm(MontrekReportForm):
    def to_html(self) -> str:
        return ""
