from django.shortcuts import redirect
from django.urls import path
from download_registry.views.download_registry_views import DownloadRegistryListView
from download_registry.views.download_registry_views import DownloadRegistryDetailView
from download_registry.views.download_registry_views import DownloadRegistryHistoryView

urlpatterns = [
    path(
        "download_registry",
        lambda _: redirect("download_registry_list"),
        name="download_registry",
    ),
    path(
        "download_registry/list",
        DownloadRegistryListView.as_view(),
        name="download_registry_list",
    ),
    path(
        "download_registry/<int:pk>/details",
        DownloadRegistryDetailView.as_view(),
        name="download_registry_details",
    ),
    path(
        "download_registry/<int:pk>/history",
        DownloadRegistryHistoryView.as_view(),
        name="download_registry_history",
    ),
]
