import logging
from typing import Protocol
from urllib.parse import urlencode

from django.http import HttpResponseRedirect
from reporting.forms import MontrekReportForm, NoMontrekReportForm

logger = logging.getLogger(__name__)


class HasFormMethods(Protocol):
    def form_invalid(self, form): ...


class ViewFormMixin(HasFormMethods):
    report_form_class = NoMontrekReportForm
    _report_form: MontrekReportForm | None = None

    @property
    def report_form(self) -> MontrekReportForm:
        if self._report_form is None:
            self._report_form = self.report_form_class()
        return self._report_form

    def post_form(self, request, *args, **kwargs):
        form = self.report_form_class(request.POST)
        if form.is_valid():
            # Build query string from cleaned_data
            params = {}
            for k, v in form.cleaned_data.items():
                # Normalize booleans to the strings your GET branch expects
                if isinstance(v, bool):
                    params[k] = "true" if v else "false"
                elif v is not None:
                    params[k] = v

            query = urlencode(params, doseq=True)  # doseq handles lists/multi-selects
            url = request.path
            if query:
                url = f"{url}?{query}"

            return HttpResponseRedirect(url)  # triggers your get()

        # Invalid form: fall back to your invalid handler
        logger.error(f"Form errors: {form.errors}")
        return self.form_invalid(form)

    def get_form(self, request):
        self._report_form = self.report_form_class(data=request.GET)
