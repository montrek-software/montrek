from django.urls import path
from country import views

urlpatterns = [
    # path(
    #    "overview",
    #    views.AssetOverview.as_view(),
    #    name="asset",
    # ),
    path(
        "create",
        views.CountryCreateView.as_view(),
        name="country_create",
    ),
    # path(
    #    "details/<int:pk>",
    #    views.AssetDetailsView.as_view(),
    #    name="asset_details",
    # ),
    # path(
    #    "update/<int:pk>",
    #    views.AssetUpdateView.as_view(),
    #    name="asset_update",
    # ),
]
