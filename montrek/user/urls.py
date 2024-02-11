from django.urls import path

from user import views

urlpatterns = [
    path("signup/", views.MontrekSignUpView.as_view(), name="signup"),
    path("login/", views.MontrekLoginView.as_view(), name="login"),
    path(
        "logout/",
        views.MontrekLogoutView.as_view(next_page="home"),
        name="logout",
    ),
    path("password_reset/", views.MontrekPasswordResetView.as_view(template_name="user/user_base.html"), name="password_reset"),
]
