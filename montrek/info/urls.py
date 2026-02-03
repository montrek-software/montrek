from django.urls import path
from info.views import info_views as views
from info.views.download_registry_views import DownloadRegistryListView
from info.views.download_registry_views import DownloadRegistryDetailView
from info.views.download_registry_views import DownloadRegistryHistoryView

urlpatterns = [
    path("info", views.InfoVersionsView.as_view(), name="info"),
    path("admin", views.InfoAdminView.as_view(), name="admin"),
    path("db_structure", views.InfoDbStructureView.as_view(), name="db_structure"),
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
