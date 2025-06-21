from baseclasses.repositories.db.db_staller import (
    DbStaller,
    StalledDicts,
)
from django.db import transaction


class DbWriter:
    def __init__(self, db_staller: DbStaller):
        self.db_staller = db_staller

    @transaction.atomic
    def write(self):
        self.write_hubs()
        self.write_updated_hubs()
        self.write_hub_value_dates()
        self.write_new_satellites()
        self.write_updated_satellites()
        self.write_links()
        self.write_updated_links()

    def write_hubs(self):
        new_hubs = self.db_staller.get_hubs()
        self._bulk_create(new_hubs)

    def write_updated_hubs(self):
        updated_hubs = self.db_staller.get_updated_hubs()
        self._bulk_update(updated_hubs)

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

    def write_links(self):
        links = self.db_staller.get_links()
        self._bulk_create(links)

    def write_updated_links(self):
        updated_links = self.db_staller.get_updated_links()
        self._bulk_update(updated_links)

    def _bulk_create(self, new_objects: StalledDicts):
        for obj_type, objs in new_objects.items():
            unsaved_objects = [obj for obj in objs if obj.pk is None]
            obj_type.objects.bulk_create(unsaved_objects)

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
        for sat_class, sats in new_satellites.items():
            for sat in sats:
                if sat_class.is_timeseries:
                    sat.hub_value_date_id = sat.hub_value_date.id
                else:
                    sat.hub_entity_id = sat.hub_entity.id
                sat.get_hash_identifier
                sat.get_hash_value
