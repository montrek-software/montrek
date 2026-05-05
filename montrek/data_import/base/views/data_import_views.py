from process_pipeline.views.process_pipeline_view import ProcessPipelineViewABC


class DataImportView(ProcessPipelineViewABC):
    def process(self):
        self.manager.process_import_data()
