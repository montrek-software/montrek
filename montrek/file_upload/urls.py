from django.urls import path
from file_upload import views

urlpatterns = [
    path(
        "upload_transaction_to_account_file/<int:account_id>/",
        views.upload_transaction_to_account_file,
        name="upload_transaction_to_account_file",
    ),
    path(
        "download_upload_file/<int:upload_registry_id>/",
        views.download_upload_file,
        name="download_upload_file",
    ),
]
