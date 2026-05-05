from process_pipeline.tasks.montrek_pipeline_task import MontrekPipelineTask


class DataImportTask(MontrekPipelineTask):
    def run(self, session_data, import_data=None, pipeline_data=None, **kwargs):
        return super().run(
            session_data,
            pipeline_data={"import_data": import_data or {}},
        )
