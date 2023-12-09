from django.urls import path
from baseclasses import views

urlpatterns = [
    path("<int:pk>/details", views.MontrekTemplateView.as_view(), name="dummy_detail"),
]
