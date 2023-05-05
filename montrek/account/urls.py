from django.urls import path
from account import views

urlpatterns = [
    path('new', views.account_new, name='account_new'),
    path('new_form', views.account_new_form, name='account_new_form'),
    path('list', views.account_list, name='account_list'),
    path('<int:account_id>/view', views.account_view, name='account_view'),
    path('<int:account_id>/delete', views.account_delete, name='account_delete'),
    path('<int:account_id>/delete_form', views.account_delete_form, name='account_delete_form'),
]
