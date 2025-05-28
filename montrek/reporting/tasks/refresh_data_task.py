from baseclasses.managers.montrek_manager import MontrekManager
from tasks.montrek_task import MontrekTask


class RefreshDataTask(MontrekTask):
    def __init__(self, manager_class: type[MontrekManager]):
        self.manager_class = manager_class
        task_name = f"{manager_class.__module__}.{manager_class.__name__}_refresh_data"
        super().__init__(task_name)

    def run(self) -> str:
        self.manager_class().repository.store_in_view_model()
        return "Refreshed data"
