from typing import TextIO
from django.shortcuts import render
from django.http import HttpResponseRedirect
from file_upload.forms import UploadFileForm
from file_upload.models import FileUploadRegistryHub
from file_upload.models import FileUploadRegistryStaticSatellite
from file_upload.models import FileUploadFileStaticSatellite
from file_upload.models import FileUploadFileHub
from link_tables.models import FileUploadRegistryFileUploadFileLink
from baseclasses.model_utils import update_satellite
from baseclasses.model_utils import new_link_entry

from account.models import AccountHub

# Create your views here.

def upload_transaction_to_account_file(request, account_id:int, credit_institution_id:int):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # handle_uploaded_file(request.FILES['file'])
            return HttpResponseRedirect('/success/url/')
    else:
        form = UploadFileForm()
    return render(request, 'upload_transaction_to_account_form.html', {'form': form})

def upload_file_upload_registry(file: TextIO) -> FileUploadRegistryStaticSatellite:
    fileuploadregistryhub = FileUploadRegistryHub.objects.create()
    fileuploadregistrystaticsattelite_pend = FileUploadRegistryStaticSatellite.objects.create(
        hub_entity = fileuploadregistryhub,
        file_name=file.name,
    )
    uploadedfile = upload_file(file)
    new_link_entry(
        from_hub = fileuploadregistrystaticsattelite_pend.hub_entity,
        to_hub = uploadedfile.hub_entity,
        link_table=FileUploadRegistryFileUploadFileLink,
    )
    fileuploadregistrystaticsattelite_upd = update_satellite(
        fileuploadregistrystaticsattelite_pend,
        upload_status='uploaded',
    )

    return fileuploadregistrystaticsattelite_upd

def upload_file(file: TextIO) -> FileUploadFileStaticSatellite:
    fileuploadhub = FileUploadFileHub.objects.create()
    fileuploadstaticsatellite = FileUploadFileStaticSatellite.objects.create(
        hub_entity = fileuploadhub,
        file=file,
    )
    return fileuploadstaticsatellite

def get_file_satellite_from_registry_satellite(
    registry_satellite: FileUploadRegistryStaticSatellite
):
    link = FileUploadRegistryFileUploadFileLink.objects.get(
        from_hub=registry_satellite.hub_entity
    )
    file_satellite = FileUploadFileStaticSatellite.objects.get(
        hub_entity=link.to_hub
    )
    return file_satellite
