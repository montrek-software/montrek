from django.apps import AppConfig


class ReportingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reporting"

    def ready(self):
        from baseclasses.constants import PdfGenMethod
        from baseclasses.view_plugins import ViewPlugins

        from reporting.managers.montrek_table_manager import HistoryDataTableManager
        from reporting.modules.pdf_responses import PdfResponses

        ViewPlugins.register_pdf_renderer(
            PdfGenMethod.WEASYPRINT, PdfResponses.weasyprint
        )
        ViewPlugins.register_pdf_renderer(PdfGenMethod.LATEX, PdfResponses.latex)
        ViewPlugins.register_history_table_manager_class(HistoryDataTableManager)
