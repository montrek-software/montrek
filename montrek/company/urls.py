from django.urls import path
from company import views

urlpatterns = [
    path(
       "overview",
       views.CompanyOverview.as_view(),
       name="company",
    ),
    path(
        "create",
        views.CompanyCreateView.as_view(),
        name="company_create",
    ),
    path(
       "details/<int:pk>",
       views.CompanyDetailsView.as_view(),
       name="company_details",
    ),
    path(
       "update/<int:pk>",
       views.CompanyUpdateView.as_view(),
       name="company_update",
    ),
]
