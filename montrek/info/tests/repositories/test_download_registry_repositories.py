"""The download registry records the act of downloading, not the data shown.

A download view may legitimately be reading a past state -- a report rendered
from a frozen risk procedure, or a redemption plan for a ``reference_date``
passed as a query parameter -- and it hands its whole session data to
``DownloadRegistryStorageManager``.  Without dropping that reference date the
write guard in ``create_by_dict`` refuses the audit entry and the download
fails with a redirect.
"""

import datetime

from django.test import TestCase
from django.utils import timezone

from info.models.download_registry_sat_models import DownloadType
from info.models.download_registry_hub_models import DownloadRegistryHub
from info.managers.download_registry_storage_managers import (
    DownloadRegistryStorageManager,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory

AN_HOUR = datetime.timedelta(hours=1)


class TestDownloadRegistryUnderAPastReferenceDate(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()

    def store(self, **extra_session_data) -> None:
        DownloadRegistryStorageManager(
            {"user_id": self.user.id, **extra_session_data}
        ).store_in_download_registry("Testbericht", DownloadType.PDF)

    def test_the_entry_is_written_despite_a_past_reference_date(self):
        self.store(reference_date=timezone.now() - AN_HOUR)
        self.assertEqual(DownloadRegistryHub.objects.count(), 1)

    def test_the_entry_is_written_without_a_reference_date(self):
        self.store()
        self.assertEqual(DownloadRegistryHub.objects.count(), 1)

    def test_the_reference_date_does_not_leak_into_the_repository(self):
        manager = DownloadRegistryStorageManager(
            {"user_id": self.user.id, "reference_date": timezone.now() - AN_HOUR}
        )
        self.assertIsNone(manager.repository.explicit_reference_date)
