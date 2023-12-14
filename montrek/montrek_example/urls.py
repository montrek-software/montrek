from django.urls import path
from montrek_example import views

urlpatterns = [
    path("a/create", views.MontrekExampleACreate.as_view(), name="montrek_example_a_create"),
]
