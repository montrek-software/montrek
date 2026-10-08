from django.urls import path

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

urlpatterns = [
    path(
        "sftp_import_source/list",
        SftpImportSourceListView.as_view(),
        name="sftp_import_source_list",
    ),
    path(
        "sftp_import_source/create",
        SftpImportSourceCreateView.as_view(),
        name="sftp_import_source_create",
    ),
    path(
        "sftp_import_source/<int:pk>/delete",
        SftpImportSourceDeleteView.as_view(),
        name="sftp_import_source_delete",
    ),
    path(
        "sftp_import_source/<int:pk>/update",
        SftpImportSourceUpdateView.as_view(),
        name="sftp_import_source_update",
    ),
    path(
        "sftp_import_source/<int:pk>/details",
        SftpImportSourceDetailView.as_view(),
        name="sftp_import_source_details",
    ),
    path(
        "sftp_import_source/<int:pk>/imported_files",
        SftpImportSourceImportedFilesView.as_view(),
        name="sftp_import_source_imported_files",
    ),
    path(
        "sftp_import_source/<int:pk>/history",
        SftpImportSourceHistoryView.as_view(),
        name="sftp_import_source_history",
    ),
    path(
        "sftp_import_source/<int:pk>/sync",
        SftpImportSourceSyncView.as_view(),
        name="sftp_import_source_sync",
    ),
]
