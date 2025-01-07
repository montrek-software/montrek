from django.urls import path
from showcase.views.sasset_views import SAssetDetailView, SAssetListView
from showcase.views.sasset_views import SAssetCreateView
from showcase.views.sasset_views import SAssetUpdateView
from showcase.views.sasset_views import SAssetDeleteView

urlpatterns = [
    path(
        "sasset/list",
        SAssetListView.as_view(),
        name="sasset_list",
    ),
    path(
        "sasset/create",
        SAssetCreateView.as_view(),
        name="sasset_create",
    ),
    path(
        "sasset/<int:pk>/delete",
        SAssetDeleteView.as_view(),
        name="sasset_delete",
    ),
    path(
        "sasset/<int:pk>/update",
        SAssetUpdateView.as_view(),
        name="sasset_update",
    ),
    path(
        "sasset/<int:pk>/details",
        SAssetDetailView.as_view(),
        name="sasset_details",
    ),
]
