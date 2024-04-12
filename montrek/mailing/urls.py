from django.urls import path
from mailing import views

urlpaterns = [
    path("overview", views.MailOverview.as_view(), name="mailing"),
    # path("send", views.SendMail.as_view(), name="send_mail"),
]
