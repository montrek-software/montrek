import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import Form
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator

from baseclasses.views import (
    MontrekDownloadView,
    MontrekListView,
    MontrekTemplateView,
)
from process_pipeline.views.process_pipeline_view import ProcessPipelineViewABC

from file_export.managers.file_export_manager import FileExportManagerABC
from file_export.managers.file_export_registry_manager import (
    FileExportRegistryManagerABC,
)

logger = logging.getLogger(__name__)


class FileExportTriggerView(ProcessPipelineViewABC):
    """Starts an export that needs no input from the user."""

    manager_class: type[FileExportManagerABC]

    def process(self):
        self.manager.trigger_export()


@method_decorator(login_required, name="dispatch")
class FileExportFormView(MontrekTemplateView):
    """Starts an export the user parameterises through a form.

    The counterpart of ``MontrekUploadFileView`` for pipelines whose input is a
    set of choices rather than a file. Whatever :meth:`get_pipeline_data` returns
    is handed to the processor, so it has to be JSON serializable — it travels to
    the Celery worker when the manager runs asynchronously.
    """

    template_name = "export_form.html"
    manager_class: type[FileExportManagerABC]
    export_form_class: type[Form]
    submit_label = "Generate"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._form: Form | None = None

    def get_template_context(self, **kwargs) -> dict:
        return {
            "export_form": self.get_form(),
            "submit_label": self.submit_label,
        }

    def get_form(self, request=None) -> Form:
        """Build the form once, so re-rendering an invalid POST keeps its errors."""
        if self._form is None:
            args = () if request is None else (request.POST, request.FILES)
            self._form = self.export_form_class(*args, **self.get_form_kwargs())
        return self._form

    def get_form_kwargs(self) -> dict:
        """Extra keyword arguments for the export form."""
        return {}

    def post(self, request, *args, **kwargs):
        form = self.get_form(request)
        if form.is_valid():
            return self.form_valid(form, request)
        return self.render_to_response(self.get_context_data())

    def form_valid(self, form, request) -> HttpResponseRedirect | TemplateResponse:
        logger.debug("Start file export process")
        result = self.manager.trigger_export(pipeline_data=self.get_pipeline_data(form))
        if result:
            messages.info(request, self.manager.message)
        else:
            messages.error(request, self.manager.message)
        logger.debug("End file export process")
        return HttpResponseRedirect(self.get_success_url())

    def get_pipeline_data(self, form: Form) -> dict:
        """Return what the processor needs from the validated form."""
        return {}

    def get_success_url(self) -> str:
        raise NotImplementedError("get_success_url not implemented")


class FileExportDownloadView(MontrekDownloadView):
    manager_class: type[FileExportRegistryManagerABC]


class FileExportRegistryListView(MontrekListView):
    manager_class: type[FileExportRegistryManagerABC]
