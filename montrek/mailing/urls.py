from django.urls import path
from mailing import views

urlpatterns = [
    path("overview", views.MailOverviewListView.as_view(), name="mailing"),
    # path("send", views.SendMail.as_view(), name="send_mail"),
]
