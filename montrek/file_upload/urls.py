from django.urls import path
from file_upload import views

urlpatterns = [
    path(
        "<int:pk>/download",
        views.MontrekDownloadFileView.as_view(),
        name="montrek_download_file",
    ),
    path(
        "<int:pk>/download/log",
        views.MontrekDownloadLogFileView.as_view(),
        name="montrek_download_log_file",
    ),
    path(
        "",
        views.FileUploadRegistryListView.as_view(),
        name="montrek_upload_file",
    ),
]
