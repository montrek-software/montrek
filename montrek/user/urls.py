from django.urls import path

from user import views

urlpatterns = [
    path("signup/", views.MontrekSignUpView.as_view(), name="signup"),
    path("login/", views.MontrekLoginView.as_view(), name="login"),
    path("logout/", views.MontrekLogoutView.as_view(), name="logout"),
    path(
        "password_reset/",
        views.MontrekPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password_reset_confirm/<uidb64>/<token>/",
        views.MontrekPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password_reset_complete",
        views.MontrekPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
