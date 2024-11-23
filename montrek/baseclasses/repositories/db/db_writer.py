from baseclasses.repositories.db.db_staller import DbStaller


class DbWriter:
    def __init__(self, db_staller: DbStaller):
        self.db_staller = db_staller

    def write(self):
        self.write_new_satellites()

    def write_new_satellites(self):
        new_satellites = self.db_staller.get_new_satellites()
        for sat_type, sats in new_satellites.items():
            sat_type.objects.bulk_create(sats)
