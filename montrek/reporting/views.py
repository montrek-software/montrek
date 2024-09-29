import os
from django.conf import settings
from django.http import HttpResponse, Http404

# Create your views here.


def download_reporting_file_view(request, file_path: str):
    file_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if not os.path.exists(file_path):
        raise Http404
    with open(file_path, "rb") as file:
        response = HttpResponse(file.read(), content_type="application/octet-stream")
        response[
            "Content-Disposition"
        ] = f"attachment; filename={os.path.basename(file_path)}"
        os.remove(file_path)
        return response
