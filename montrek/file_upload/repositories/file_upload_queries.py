from django.apps import apps

def file_upload_registry_hub():
    return apps.get_model('file_upload', 'FileUploadRegistryHub')

def account_file_upload_registry_link():
    return apps.get_model('link_tables', 'AccountFileUploadRegistryLink')

def file_upload_registry_file_upload_file_link():
    return apps.get_model('link_tables', 'FileUploadRegistryFileUploadFileLink')

def file_upload_file_static_satellite():
    return apps.get_model('file_upload', 'FileUploadFileStaticSatellite')

def get_account_hub_from_file_upload_registry_satellite(
    file_upload_registry
):
    account_hub = account_file_upload_registry_link().objects.get(
        to_hub=file_upload_registry.hub_entity,
    ).from_hub
    return account_hub

def get_file_satellite_from_registry_satellite(
    registry_satellite
):
    link = file_upload_registry_file_upload_file_link().objects.get(
        from_hub=registry_satellite.hub_entity
    )
    file_satellite = file_upload_file_static_satellite().objects.get(
        hub_entity=link.to_hub
    )
    return file_satellite

