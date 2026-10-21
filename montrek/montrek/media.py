"""Serves MEDIA_ROOT to logged-in users.

Uploads are only handed out through `serve_media`, which checks the login
first. Paths in LOGIN_EXEMPT_PATHS stay public, such as images a public page
embeds.

With MEDIA_X_ACCEL_REDIRECT set, the view answers with an X-Accel-Redirect to
that internal nginx location and nginx sends the file. That is how it runs
behind the compose nginx. Without it, as under runserver or on a host without
nginx, Django streams the file itself.
"""

import mimetypes
from pathlib import Path
from urllib.parse import quote

from baseclasses.utils import htmx_aware_redirect
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.http.response import HttpResponseBase
from django.utils.cache import patch_cache_control
from django.views.decorators.http import require_safe
from middleware.login_required_middleware import is_login_exempt_path


@require_safe
def serve_media(request, path: str) -> HttpResponseBase:
    # Before the exemption check: a request that reaches Django without
    # nginx normalizing it, such as a/../b, would otherwise be judged by its
    # public prefix and then served from where it points.
    if any(part in (".", "..") for part in path.split("/")):
        raise Http404
    # LoginRequiredMiddleware also lets through REST API calls by a query
    # parameter, which must not open up every upload, so the login is checked
    # here again.
    if not request.user.is_authenticated and not is_login_exempt_path(request.path):
        return htmx_aware_redirect(request, str(settings.LOGIN_URL))
    # Resolved, so a symlink under MEDIA_ROOT that points out of it is not
    # followed.
    media_root = Path(settings.MEDIA_ROOT).resolve()
    file_path = (media_root / path).resolve()
    if not file_path.is_relative_to(media_root) or not file_path.is_file():
        raise Http404
    response: HttpResponseBase
    if accel_location := settings.MEDIA_X_ACCEL_REDIRECT:
        relative_path = file_path.relative_to(media_root)
        response = HttpResponse(
            content_type=mimetypes.guess_type(file_path.name)[0]
            or "application/octet-stream"
        )
        response["X-Accel-Redirect"] = quote(
            accel_location.rstrip("/") + "/" + relative_path.as_posix()
        )
    else:
        response = FileResponse(file_path.open("rb"))
    if request.user.is_authenticated:
        # The browser may keep it, but has to ask again before each use, so a
        # file is not shown from the cache after the session has ended.
        patch_cache_control(response, private=True, no_cache=True)
    else:
        patch_cache_control(response, public=True, max_age=30 * 24 * 60 * 60)
    return response
