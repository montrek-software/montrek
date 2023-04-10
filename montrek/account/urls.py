from django.urls import path
from account import views

urlpatterns = [
    path('new', views.new_account, name='new_account'),
    path('new_form', views.new_account_form, name='new_account_form'),
]
