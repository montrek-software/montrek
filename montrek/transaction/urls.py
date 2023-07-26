from django.urls import path
from transaction import views

urlpatterns = [
    path(
        "transaction_add_form/<int:account_id>",
        views.transaction_add_form,
        name="transaction_add_form",
    ),
    path(
        "transaction_add/<int:account_id>",
        views.transaction_add,
        name="transaction_add",
    ),
]
