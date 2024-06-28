from .settings import *  # Import base settings from settings.py

# Override any settings for testing purposes

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EMAIL_TEMPLATE = "mail_templates/montrek_mail_template.html"
MEDIA_ROOT = "Blummi"
