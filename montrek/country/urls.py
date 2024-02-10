from django.urls import path
from country import views

urlpatterns = [
    path(
       "overview",
       views.CountryOverview.as_view(),
       name="country",
    ),
    path(
        "create",
        views.CountryCreateView.as_view(),
        name="country_create",
    ),
    path(
       "details/<int:pk>",
       views.CountryDetailsView.as_view(),
       name="country_details",
    ),
    path(
       "update/<int:pk>",
       views.CountryUpdateView.as_view(),
       name="country_update",
    ),
]
