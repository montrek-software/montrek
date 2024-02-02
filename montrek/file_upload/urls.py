from django.urls import path
from file_upload import views

urlpatterns = [
    path(
        "<int:pk>/download",
        views.MontrekDownloadFileView.as_view(),
        name="montrek_download_file",
    ),
]
