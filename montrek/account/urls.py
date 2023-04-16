from django.urls import path
from account import views

urlpatterns = [
    path('new', views.account_new, name='account_new'),
    path('new_form', views.account_new_form, name='account_new_form'),
    path('list', views.account_list, name='account_list'),
    path('<int:account_id>/', views.account_view, name='account_view'),
]
