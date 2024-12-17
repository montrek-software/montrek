from tasks.montrek_task import MontrekTask


class DownloadTableTask(MontrekTask):
    is_register_on_subclass_init = False

    @classmethod
    def register_task(cls, **kwargs):
        manager_class = kwargs.get("manager_class")
        task_name = f"{manager_class.__module__}.{manager_class.__name__}_download_task"
        cls.name = task_name
        cls.manager_class = manager_class
        super().register_task(**kwargs)

    def run(self, *args, filetype, session_data: dict, **kwargs) -> str:
        self.manager_class(session_data).send_table_by_mail(filetype)
        return "Table sent by mail."
