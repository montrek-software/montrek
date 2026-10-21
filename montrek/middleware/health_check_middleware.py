import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)

LIVENESS_PATH = "/health"
READINESS_PATH = "/health/ready"


class HealthCheckMiddleware:
    """Answers the container health checks.

    It has to come first in MIDDLEWARE. A health check is sent to the container
    address over plain HTTP, so it fails the ALLOWED_HOSTS validation that
    CommonMiddleware triggers and is redirected to https by SecurityMiddleware,
    and LoginRequiredMiddleware would redirect it to the login page. The
    responses carry nothing but the status, so answering them for any host is
    safe.

    The liveness check only proves the process serves requests. The readiness
    check also needs the database, so a load balancer stops routing to an
    instance that has lost it while the orchestrator does not restart it for
    that.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip("/")
        if path == LIVENESS_PATH:
            return JsonResponse({"status": "ok"})
        if path == READINESS_PATH:
            return self.readiness()
        return self.get_response(request)

    def readiness(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except DatabaseError:
            logger.exception("Readiness check failed: database unreachable")
            return JsonResponse({"status": "unavailable"}, status=503)
        return JsonResponse({"status": "ok"})
