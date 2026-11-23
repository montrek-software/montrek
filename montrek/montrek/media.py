"""Serves the default storage's files to logged-in users.

Uploads are only handed out through `serve_media`, which checks the login
first. Paths in LOGIN_EXEMPT_PATHS stay public, such as images a public page
embeds.

From a filesystem storage, MEDIA_ROOT: with MEDIA_X_ACCEL_REDIRECT set, the
view answers with an X-Accel-Redirect to that internal nginx location and nginx
sends the file. That is how it runs behind the compose nginx. Without it, as
under runserver or on a host without nginx, Django streams the file itself.

From any other storage, such as a private object storage container, it
redirects to the URL the storage hands out for the file, a signed one that
expires. A storage without URLs of its own, whose url() points back here, is
streamed by Django.
"""

import mimetypes
from pathlib import Path
from urllib.parse import quote, urlparse

from baseclasses.utils import htmx_aware_redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect
from django.http.response import HttpResponseBase
from django.utils.cache import patch_cache_control
from django.views.decorators.http import require_safe
from middleware.login_required_middleware import is_login_exempt_path

PUBLIC_MAX_AGE = 30 * 24 * 60 * 60


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
    media_file = MediaFile(path)
    if isinstance(default_storage, FileSystemStorage):
        response = media_file.from_disk()
    else:
        response = media_file.from_storage()
    if request.user.is_authenticated or isinstance(response, HttpResponseRedirect):
        # The browser may keep it, but has to ask again before each use, so a
        # file is not shown from the cache after the session has ended, and a
        # redirect not followed after its signed URL has expired.
        patch_cache_control(response, private=True, no_cache=True)
    else:
        patch_cache_control(response, public=True, max_age=PUBLIC_MAX_AGE)
    return response


class MediaFile:
    """The response for one file of the default storage, by its name."""

    def __init__(self, path: str):
        self.path = path

    def from_disk(self) -> HttpResponseBase:
        # Resolved, so a symlink under MEDIA_ROOT that points out of it is not
        # followed.
        media_root = Path(settings.MEDIA_ROOT).resolve()
        file_path = (media_root / self.path).resolve()
        if not file_path.is_relative_to(media_root) or not file_path.is_file():
            raise Http404
        if accel_location := settings.MEDIA_X_ACCEL_REDIRECT:
            response = HttpResponse(content_type=self.content_type(file_path.name))
            response["X-Accel-Redirect"] = quote(
                accel_location.rstrip("/")
                + "/"
                + file_path.relative_to(media_root).as_posix()
            )
            return response
        return FileResponse(file_path.open("rb"))

    def from_storage(self) -> HttpResponseBase:
        # On an object storage a directory is only a prefix of the stored
        # names, so exists() is False for it, as for a missing file.
        if not self.path or not default_storage.exists(self.path):
            raise Http404
        url = default_storage.url(self.path)
        if urlparse(url).netloc:
            return HttpResponseRedirect(url)
        return FileResponse(
            default_storage.open(self.path, "rb"),
            content_type=self.content_type(self.path),
        )

    @staticmethod
    def content_type(name: str) -> str:
        return mimetypes.guess_type(name)[0] or "application/octet-stream"
