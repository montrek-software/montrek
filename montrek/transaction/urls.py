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
        "<int:pk>/view/",
        views.TransactionSatelliteDetailView.as_view(),
        name="transaction_view",
    ),
]
