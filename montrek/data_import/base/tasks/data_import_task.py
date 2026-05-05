from process_pipeline.tasks.montrek_pipeline_task import MontrekPipelineTask


class DataImportTask(MontrekPipelineTask):
    def run(self, session_data, import_data=None, pipeline_data=None, **kwargs):
        merged_pipeline_data = dict(pipeline_data or {})
        merged_pipeline_data["import_data"] = import_data or {}

        return super().run(
            session_data,
            pipeline_data=merged_pipeline_data,
        )
