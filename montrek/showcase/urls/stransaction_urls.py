from django.urls import path
import showcase.views.stransaction_views as views

urlpatterns = [
    path(
        "stransaction/list",
        views.STransactionListView.as_view(),
        name="stransaction_list",
    ),
    path(
        "stransaction/create",
        views.STransactionCreateView.as_view(),
        name="stransaction_create",
    ),
    path(
        "stransaction/<int:pk>/delete",
        views.STransactionDeleteView.as_view(),
        name="stransaction_delete",
    ),
    path(
        "stransaction/<int:pk>/update",
        views.STransactionUpdateView.as_view(),
        name="stransaction_update",
    ),
    path(
        "stransaction/file_upload/registry/list",
        views.STransactionFURegistryView.as_view(),
        name="stransaction_fu_registry_list",
    ),
    path(
        "stransaction/file_upload/download/<int:pk>",
        views.STransactionDownloadFileView.as_view(),
        name="stransaction_download_file",
    ),
    path(
        "stransaction/file_upload/upload",
        views.STransactionUploadFileView.as_view(),
        name="stransaction_upload_file",
    ),
]
