from django.urls import path
from file_upload import views

urlpatterns = [
    path(
        "upload_transaction_to_account_file/<int:account_id>/",
        views.upload_transaction_to_account_file,
        name="upload_transaction_to_account_file",
    ),
]
