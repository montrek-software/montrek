from unittest import mock

from django.urls import reverse

from sftp.repositories.sftp_import_source_repositories import (
    SftpImportSourceRepository,
)
from sftp.tests.factories.sftp_connection_sat_factories import (
    SftpConnectionSatelliteFactory,
)
from sftp.tests.factories.sftp_import_source_factories import (
    LinkSftpImportedFileSftpImportSourceFactory,
    LinkSftpImportSourceSftpConnectionFactory,
    SftpImportedFileSatelliteFactory,
    SftpImportSourceSatelliteFactory,
)
from sftp.views.sftp_import_source_views import (
    SftpImportSourceCreateView,
    SftpImportSourceDeleteView,
    SftpImportSourceDetailView,
    SftpImportSourceHistoryView,
    SftpImportSourceImportedFilesView,
    SftpImportSourceListView,
    SftpImportSourceSyncView,
    SftpImportSourceUpdateView,
)
from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekDeleteViewTestCase,
    MontrekListViewTestCase,
    MontrekPostActionViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekViewTestCase,
)


A1_UPLOAD_KEY = "montrek_example.managers.a1_file_upload_manager.A1FileUploadManager"


def build_linked_source(**kwargs):
    connection = SftpConnectionSatelliteFactory(host="sftp.example.com")
    source = SftpImportSourceSatelliteFactory(**kwargs)
    LinkSftpImportSourceSftpConnectionFactory(
        hub_in=source.hub_entity, hub_out=connection.hub_entity
    )
    return source, connection


class TestSftpImportSourceCreateView(MontrekCreateViewTestCase):
    viewname = "sftp_import_source_create"
    view_class = SftpImportSourceCreateView

    def build_factories(self):
        self.connection = SftpConnectionSatelliteFactory(host="sftp.example.com")

    def creation_data(self):
        return {
            "name": "Daily positions",
            "remote_dir": "outbox",
            "file_pattern": "positions_*.csv",
            "upload_type": A1_UPLOAD_KEY,
            "min_file_age_seconds": 120,
            "processed_dir": "done",
            "is_active": True,
            "link_sftp_import_source_sftp_connection": (
                self.connection.get_hub_value_date().pk
            ),
        }

    def additional_assertions(self, created_object):
        self.assertEqual(
            created_object.sftp_connection_hub_id, self.connection.hub_entity_id
        )
        self.assertEqual(created_object.sftp_host, "sftp.example.com")

    def test_pipeline_parameters_are_stored_as_json(self):
        data = self.creation_data()
        data["name"] = "With parameters"
        data["pipeline_parameters"] = '{"overwrite": false}'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        created = SftpImportSourceRepository().receive().get(name="With parameters")
        self.assertEqual(created.pipeline_parameters, {"overwrite": False})

    def test_pipeline_parameters_must_be_an_object(self):
        for parameters in ('["overwrite"]', '"overwrite"', "1"):
            with self.subTest(parameters=parameters):
                data = self.creation_data()
                data["pipeline_parameters"] = parameters
                response = self.client.post(self.url, data)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Enter a JSON object")
        self.assertFalse(SftpImportSourceRepository().receive().exists())

    def test_pipeline_parameters_cannot_set_user(self):
        data = self.creation_data()
        data["pipeline_parameters"] = '{"user_id": 1}'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user_id cannot be set")
        self.assertFalse(SftpImportSourceRepository().receive().exists())

    def test_poll_status_is_not_editable(self):
        form = self.response.context["form"]
        self.assertNotIn("last_poll_status", form.fields)
        self.assertNotIn("status_changed_at", form.fields)

    def test_unregistered_upload_type_is_rejected(self):
        data = self.creation_data()
        data["upload_type"] = "unknown"
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SftpImportSourceRepository().receive().exists())


class TestSftpImportSourceUpdateView(MontrekUpdateViewTestCase):
    viewname = "sftp_import_source_update"
    view_class = SftpImportSourceUpdateView

    def build_factories(self):
        self.sat_obj, self.connection = build_linked_source(upload_type=A1_UPLOAD_KEY)

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}

    def update_data(self):
        return {
            "name": "Renamed",
            "link_sftp_import_source_sftp_connection": (
                self.connection.get_hub_value_date().pk
            ),
        }

    def test_connection_is_preselected(self):
        form = self.response.context["form"]
        initial = form.fields["link_sftp_import_source_sftp_connection"].initial
        self.assertEqual(initial.hub_id, self.connection.hub_entity_id)


class TestSftpImportSourceListView(MontrekListViewTestCase):
    viewname = "sftp_import_source_list"
    view_class = SftpImportSourceListView
    expected_no_of_rows = 1

    def build_factories(self):
        build_linked_source()

    def test_shows_sync_button(self):
        self.assertContains(self.response, "/sync")


class TestSftpImportSourceDeleteView(MontrekDeleteViewTestCase):
    viewname = "sftp_import_source_delete"
    view_class = SftpImportSourceDeleteView

    def build_factories(self):
        self.sat_obj = SftpImportSourceSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}


class TestSftpImportSourceDetailView(MontrekViewTestCase):
    viewname = "sftp_import_source_details"
    view_class = SftpImportSourceDetailView

    def build_factories(self):
        self.sat_obj, _ = build_linked_source(name="Daily positions")

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.hub_entity_id}

    def test_shows_source(self):
        self.assertContains(self.response, "Daily positions")
        self.assertContains(self.response, "sftp.example.com")


class TestSftpImportSourceImportedFilesView(MontrekListViewTestCase):
    viewname = "sftp_import_source_imported_files"
    view_class = SftpImportSourceImportedFilesView
    expected_no_of_rows = 1

    def build_factories(self):
        self.sat_obj, _ = build_linked_source()
        imported_file = SftpImportedFileSatelliteFactory(remote_path="/in/a.csv")
        LinkSftpImportedFileSftpImportSourceFactory(
            hub_in=imported_file.hub_entity, hub_out=self.sat_obj.hub_entity
        )
        # Of another source, so not listed
        LinkSftpImportedFileSftpImportSourceFactory(
            hub_in=SftpImportedFileSatelliteFactory().hub_entity
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.hub_entity_id}

    def test_shows_imported_file(self):
        self.assertContains(self.response, "/in/a.csv")


class TestSftpImportSourceHistoryView(MontrekViewTestCase):
    viewname = "sftp_import_source_history"
    view_class = SftpImportSourceHistoryView

    def build_factories(self):
        self.sat_obj = SftpImportSourceSatelliteFactory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.get_hub_value_date().id}


class TestSftpImportSourceSyncView(MontrekPostActionViewTestCase):
    viewname = "sftp_import_source_sync"
    view_class = SftpImportSourceSyncView

    def build_factories(self):
        self.sat_obj = SftpImportSourceSatelliteFactory()
        patcher = mock.patch(
            "sftp.managers.sftp_import_scheduler_manager."
            "sftp_import_source_sync_task.delay"
        )
        self.delay = patcher.start()
        self.addCleanup(patcher.stop)

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_obj.hub_entity_id}

    def expected_url(self) -> str:
        return reverse("sftp_import_source_list")

    def test_schedules_sync_as_requesting_user(self):
        self.delay.assert_called_once_with(
            source_hub_id=self.sat_obj.hub_entity_id, user_id=self.user.pk
        )
