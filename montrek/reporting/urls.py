from django.urls import path
from reporting import views

urlpatterns = [
    path(
        "download/<uuid:download_id>/<str:file_name>/",
        views.download_reporting_file_view,
        name="download_reporting_file",
    ),
]
