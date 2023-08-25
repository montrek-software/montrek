from typing import TextIO
from django.apps import apps

from baseclasses.repositories.db_helper import  select_satellite
from baseclasses.repositories.db_helper import get_hub_by_id
from baseclasses.repositories.db_helper import new_link_entry
from account.models import AccountHub


def file_upload_registry_hub():
    return apps.get_model("file_upload", "FileUploadRegistryHub")


def file_upload_registry_static_satellite():
    return apps.get_model("file_upload", "FileUploadRegistryStaticSatellite")


def file_upload_file_hub():
    return apps.get_model("file_upload", "FileUploadFileHub")


def file_upload_file_static_satellite():
    return apps.get_model("file_upload", "FileUploadFileStaticSatellite")


def get_account_hub_from_file_upload_registry_satellite(file_upload_registry):
    account_hub = file_upload_registry.hub_entity.link_file_upload_registry_account.all().first()
    return account_hub


def get_file_satellite_from_registry_satellite(registry_satellite):
    file_hub = registry_satellite.hub_entity.link_file_upload_registry_file_upload_file.all().first()
    return select_satellite(file_hub, file_upload_file_static_satellite())

def get_file_satellite_from_registry_hub_id(registry_hub_id: int):
    file_hub = file_upload_registry_hub().objects.get(id=registry_hub_id).link_file_upload_registry_file_upload_file.all().first()
    return select_satellite(file_hub, file_upload_file_static_satellite())


def new_file_upload_registry(account_id: int, file: TextIO):
    fileuploadregistryhub = file_upload_registry_hub().objects.create()
    fileuploadregistrystaticsattelite_pend = (
        file_upload_registry_static_satellite().objects.create(
            hub_entity=fileuploadregistryhub,
            file_name=file.name,
        )
    )
    account_hub = get_hub_by_id(account_id, AccountHub)
    new_link_entry(
        from_hub=account_hub,
        to_hub=fileuploadregistryhub,
        related_field='link_account_file_upload_registry',
    )
    return fileuploadregistrystaticsattelite_pend


def new_file_upload_file(fileuploadregistrystaticsattelite_pend, file: TextIO):
    fileuploadhub = file_upload_file_hub().objects.create()
    fileuploadfilestaticsatellite = file_upload_file_static_satellite().objects.create(
        hub_entity=fileuploadhub,
        file=file,
    )
    new_link_entry(
        from_hub=fileuploadregistrystaticsattelite_pend.hub_entity,
        to_hub=fileuploadhub,
        related_field="link_file_upload_registry_file_upload_file",
    )
    return fileuploadfilestaticsatellite

def get_upload_regisrty_files_from_account_id(account_id: int) -> list:
    account_hub = get_hub_by_id(account_id, AccountHub)
    file_upload_registry_hubs = account_hub.link_account_file_upload_registry.all()
    file_upload_registry_satellites = file_upload_registry_static_satellite().objects.filter(
        hub_entity__in=file_upload_registry_hubs
    )
    return file_upload_registry_satellites
