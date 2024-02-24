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
    path(
        "delete/<int:pk>",
        views.CompanyDeleteView.as_view(),
        name="company_delete",
    ),
    path(
        "company_ts_table/<int:pk>",
        views.CompanyTSTableView.as_view(),
        name="company_ts_table",
    ),
    path(
        "upload_file",
        views.CompanyUploadFileView.as_view(),
        name="company_upload_file",
    ),
    path(
        "uploads",
        views.CompanyUploadView.as_view(),
        name="company_view_uploads",
    ),
]
