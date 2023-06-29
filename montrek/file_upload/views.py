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
from credit_institution.model_utils import get_credit_institution_by_account_id
from file_upload.model_utils import get_account_by_file_upload_registry

# Create your views here.

def upload_transaction_to_account_file(request, account_id:int):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload_registry = upload_file_upload_registry(request.FILES['file'])
            processed_registry = process_file(upload_registry, account_id)
            return upload_file_message(request, processed_registry)
    else:
        form = UploadFileForm()
    return render(request, 'upload_transaction_to_account_form.html', {'form': form})

def upload_file_message(request, fileuploadregistry: FileUploadRegistryStaticSatellite):
    return render(request, 'upload_file_message.html', {'fileuploadregistry': fileuploadregistry})

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
) -> FileUploadFileStaticSatellite:
    link = FileUploadRegistryFileUploadFileLink.objects.get(
        from_hub=registry_satellite.hub_entity
    )
    file_satellite = FileUploadFileStaticSatellite.objects.get(
        hub_entity=link.to_hub
    )
    return file_satellite

def process_file(
    registry_satellite: FileUploadRegistryStaticSatellite,
    account_id: int,
) -> FileUploadRegistryStaticSatellite:
    if registry_satellite.upload_status != 'uploaded':
        fileuploadregistry_failed = update_satellite(
            registry_satellite,
            upload_status='failed',
            upload_message='Try to process file that has not been not uploaded',
        )
        return fileuploadregistry_failed

    file_satellite = get_file_satellite_from_registry_satellite(registry_satellite)
    account_hub = AccountHub.objects.get(pk=account_id)
    credit_institution_satellite = get_credit_institution_by_account_id(account_id)     
    if credit_institution_satellite.account_upload_method == 'none':
        credit_institution_name = credit_institution_satellite.credit_institution_name
        fileuploadregistry_failed = update_satellite(
            registry_satellite,
            upload_status='failed',
            upload_message=f'Credit Institution {credit_institution_name} provides no upload method',
        )
        return fileuploadregistry_failed
