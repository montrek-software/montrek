from django.urls import path
from mailing import views

urlpatterns = [
    path("overview", views.MailOverviewListView.as_view(), name="mailing"),
    path("send", views.SendMailView.as_view(), name="send_mail"),
    path("<int:pk>/details", views.MailDetailView.as_view(), name="mail_detail"),
]
