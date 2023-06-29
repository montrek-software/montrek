from django.apps import apps

def file_upload_registry_hub():
    return apps.get.model('file_upload', 'FileUploadRegistryHub')

def account_file_upload_registry_link():
    return apps.get.model('link_tables', 'AccountFileUploadRegistryLink')

def get_account_by_file_upload_registry(file_upload_registry):
    account_hub = account_file_upload_registry_link().objects.get(
        to_hub=file_upload_registry.hub_entity,
    )[0].from_hub
    return account_hub

