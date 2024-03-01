import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "montrek.settings")
celery_app = Celery(
    "montrek",
    broker="redis://redis:6379",
    backend="redis://redis:6379",
)
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()


@celery_app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
