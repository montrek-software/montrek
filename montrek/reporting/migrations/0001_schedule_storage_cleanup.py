from django.db import migrations

TASK_NAME = "reporting.tasks.cleanup_task.ReportingStorageCleanupTask"


def schedule(apps, schema_editor):
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    interval, _ = IntervalSchedule.objects.get_or_create(every=1, period="days")
    PeriodicTask.objects.get_or_create(
        name=TASK_NAME, defaults={"task": TASK_NAME, "interval": interval}
    )


def unschedule(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name=TASK_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [migrations.RunPython(schedule, unschedule)]
