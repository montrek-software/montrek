from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS api_import_mockapiregistryhubvaluedate",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS api_import_mockapiregistryhub CASCADE",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
