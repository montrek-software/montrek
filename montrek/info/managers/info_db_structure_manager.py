from info.dataclasses.db_structure_container import DbStructureContainer


class InfoDbStructureManager:
    def get_db_structure_container(self):
        return DbStructureContainer(hubs=[])
