from tasks.montrek_task import MontrekTask
from baseclasses.managers.montrek_manager import MontrekManager


class RefreshDataTask(MontrekTask):
    def set_manager(self, manager: MontrekManager):
        self.manager = manager

    def run(self):
        self.manager.repository.store_in_view_model()
