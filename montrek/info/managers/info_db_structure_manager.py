from info.dataclasses.db_structure_container import DbStructureContainer


class InfoDbStructureManager:
    def get_db_structure_container(self) -> dict[str, DbStructureContainer]:
        return {"info": DbStructureContainer(hubs=[])}
