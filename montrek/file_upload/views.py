from typing import TextIO
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import FileResponse
from file_upload.forms import UploadFileForm
from file_upload.managers.transactions_upload_manager import (
    process_upload_transaction_file,
)
from file_upload.repositories.file_upload_queries import (
    get_file_satellite_from_registry_hub_id,
)
from file_upload.models import FileUploadRegistryStaticSatellite

# Create your views here.


def upload_transaction_to_account_file(request, account_id: int):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload_registry = process_upload_transaction_file(
                account_id,
                request.FILES["file"],
            )
            return upload_file_message(request, upload_registry, account_id)
    else:
        form = UploadFileForm()
    return render(request, "upload_transaction_to_account_form.html", {"form": form})


def upload_file_message(
    request, fileuploadregistry: FileUploadRegistryStaticSatellite, account_id: int
):
    return render(
        request,
        "upload_file_message.html",
        {"fileuploadregistry": fileuploadregistry, "account_id": account_id},
    )

def download_upload_file(
    request, upload_registry_id: int
):
    upload_file_file_sat = get_file_satellite_from_registry_hub_id(upload_registry_id)
    return FileResponse(upload_file_file_sat.file, as_attachment=True)
