from django.urls import path
from transaction import views

urlpatterns = [
    path(
        "add_form/<int:account_id>",
        views.transaction_add_form,
        name="transaction_add_form",
    ),
    path(
        "add/<int:account_id>",
        views.transaction_add,
        name="transaction_add",
    ),
    path(
        "<int:transaction_id>/view/",
        views.transaction_view,
        name="transaction_view",
    ),
]
