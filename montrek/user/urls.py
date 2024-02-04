from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordResetView

from user import views

urlpatterns = [
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "logout/",
        LogoutView.as_view(template_name="user/logout.html", next_page="home"),
        name="logout",
    ),
    path("password_reset/", views.PasswordResetView.as_view(template_name="user/user_base.html"), name="password_reset")
]
