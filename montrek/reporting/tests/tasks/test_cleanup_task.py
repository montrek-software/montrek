import datetime
from unittest import mock

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase
from django.utils import timezone
from django_celery_beat.models import PeriodicTask  # type: ignore[import-untyped]
from reporting.tasks.cleanup_task import (
    MAX_AGE,
    ReportingStorageCleanupTask,
    reporting_storage_cleanup_task,
)
from testing.decorators.object_storage import object_storage


@object_storage
class TestReportingStorageCleanupTask(TestCase):
    def test_deletes_mailed_tables_and_report_pdfs_past_max_age(self):
        names = [
            default_storage.save(name, ContentFile(b"x"))
            for name in (
                "reporting_downloads/1/abc/table.csv",
                "latex/abc/document.pdf",
                "file_exports/export.csv",
            )
        ]
        past_max_age = timezone.now() + MAX_AGE + datetime.timedelta(days=1)

        with mock.patch.object(timezone, "now", return_value=past_max_age):
            result = reporting_storage_cleanup_task.run()

        self.assertEqual(result, "Deleted 2 files")
        self.assertEqual(
            [default_storage.exists(name) for name in names], [False, False, True]
        )

    def test_keeps_files_within_max_age(self):
        name = default_storage.save("latex/abc/document.pdf", ContentFile(b"x"))
        self.assertEqual(reporting_storage_cleanup_task.run(), "Deleted 0 files")
        self.assertTrue(default_storage.exists(name))

    def test_is_scheduled_daily(self):
        task_name = (
            f"{ReportingStorageCleanupTask.__module__}."
            f"{ReportingStorageCleanupTask.__name__}"
        )
        periodic_task = PeriodicTask.objects.get(name=task_name)
        self.assertEqual(periodic_task.task, reporting_storage_cleanup_task.name)
        self.assertEqual(
            (periodic_task.interval.every, periodic_task.interval.period), (1, "days")
        )
