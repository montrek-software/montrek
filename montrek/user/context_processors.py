from django.conf import settings


def sign_in(_request):
    # For the navbar: which of the app's own sign-in pages it links to.
    return {
        "allow_password_login": settings.ALLOW_PASSWORD_LOGIN,
        "allow_signup": settings.ALLOW_SIGNUP,
    }
