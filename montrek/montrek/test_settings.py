from .settings import *  # Import base settings from settings.py

# Override any settings for testing purposes

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EMAIL_TEMPLATE = f"{STATIC_ROOT}/mail_templates/montrek_template.html"
