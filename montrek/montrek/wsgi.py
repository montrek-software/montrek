"""
WSGI config for montrek project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.urls import get_resolver

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "montrek.settings")

application = get_wsgi_application()

# Django imports the URLconf, and with it every app's views, only on the first
# request. Gunicorn loads this module in each worker before the worker accepts
# connections, so importing it here keeps that cost (seconds) away from the
# first request a new or recycled worker serves. It needs no database.
_ = get_resolver().reverse_dict
