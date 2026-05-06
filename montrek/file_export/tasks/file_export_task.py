from process_pipeline.tasks.montrek_pipeline_task import MontrekPipelineTask


# Stub for async export tasks; all orchestration lives in the pipeline task.
class FileExportTask(MontrekPipelineTask): ...
