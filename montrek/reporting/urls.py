from django.urls import path
from reporting import views

urlpatterns = [
    path(
        "download/<path:file_path>/",
        views.download_reporting_file_view,
        name="download_reporting_file",
    ),
]
