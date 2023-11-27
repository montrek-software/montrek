from django.urls import path
from credit_institution import views

urlpatterns = [
    path("", views.CreditInstitutionOverview.as_view(), name="credit_institution"),
]
