from django.urls import path
from currency import views

urlpatterns = [
    path('', views.CurrencyOverview.as_view(), name='currency'),
    path("<int:pk>/details", views.CurrencyDetailView.as_view(), name="currency_details"),
]
