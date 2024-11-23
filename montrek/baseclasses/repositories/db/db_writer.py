from baseclasses.repositories.db.db_staller import (
    DbStaller,
    StalledDicts,
)


class DbWriter:
    def __init__(self, db_staller: DbStaller):
        self.db_staller = db_staller

    def write(self):
        self.write_hubs()
        self.write_hub_value_dates()
        self.write_new_satellites()
        self.write_updated_satellites()

    def write_hubs(self):
        new_hubs = self.db_staller.get_hubs()
        self._bulk_create(new_hubs)

    def write_new_satellites(self):
        new_satellites = self.db_staller.get_new_satellites()
        self._set_sat_hashes(new_satellites)
        self._bulk_create(new_satellites)

    def write_updated_satellites(self):
        updated_satellites = self.db_staller.get_updated_satellites()
        self._bulk_update(updated_satellites)

    def write_hub_value_dates(self):
        new_hub_value_dates = self.db_staller.get_hub_value_dates()
        self._bulk_create(new_hub_value_dates)

    def _bulk_create(self, new_objects: StalledDicts):
        for obj_type, objs in new_objects.items():
            obj_type.objects.bulk_create(objs)

    def _bulk_update(self, new_objects: StalledDicts):
        for obj_type, objs in new_objects.items():
            obj_type.objects.bulk_update(
                objs,
                fields=(
                    "state_date_end",
                    "state_date_start",
                ),
            )

    def _set_sat_hashes(self, new_satellites: StalledDicts):
        for _, sats in new_satellites.items():
            for sat in sats:
                sat.hub_entity_id = sat.hub_entity.id
                sat.get_hash_identifier
                sat.get_hash_value
