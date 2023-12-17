from typing import TextIO
from file_upload.models import FileUploadFileStaticSatellite
from file_upload.models import FileUploadRegistryStaticSatellite
from file_upload.models import FileUploadRegistryHub
from file_upload.models import FileUploadFileHub
from file_upload.repositories.file_upload_queries import (
    get_account_hub_from_file_upload_registry_satellite,
)
from file_upload.repositories.file_upload_queries import new_file_upload_registry
from file_upload.repositories.file_upload_queries import new_file_upload_file
from file_upload.repositories.file_upload_queries import (
    get_file_satellite_from_registry_satellite,
)
from baseclasses.repositories.db_helper import update_satellite_from_satellite
from baseclasses.repositories.db_helper import get_hub_by_id
from account.managers.transaction_upload_methods import upload_dkb_transactions
from account.repositories.account_repository import AccountRepository


def process_upload_transaction_file(account_id: int, file: TextIO):
    fileuploadregistrysat = _init_file_upload_registry(account_id, file)
    fileuploadregistrysat = _upload_file_to_registry(fileuploadregistrysat, file)
    fileuploadregistrysat = _upload_transactions_to_account_manager(
        fileuploadregistrysat
    )
    return fileuploadregistrysat


def _init_file_upload_registry(account_id: int, file: TextIO):
    fileuploadregistrystaticsattelite_pend = new_file_upload_registry(
        account_id,
        file,
    )
    return fileuploadregistrystaticsattelite_pend


def _upload_transactions_to_account_manager(
    upload_registry_sat: FileUploadFileStaticSatellite,
) -> FileUploadRegistryStaticSatellite:
    if upload_registry_sat.upload_status != "uploaded":
        return _upload_error_file_not_uploaded_registry(upload_registry_sat)
    account_hub = get_account_hub_from_file_upload_registry_satellite(
        upload_registry_sat
    )
    account_traits = AccountRepository({}).std_queryset().get(pk=account_hub.pk)
    credit_institution_upload_method = account_traits.creditinstitutionstaticsatellite__account_upload_method
    credit_institution_name = account_traits.creditinstitutionstaticsatellite__credit_institution_name

    if credit_institution_upload_method == "none":
        return _upload_error_account_upload_method_none(
            upload_registry_sat, credit_institution_name
        )
    if credit_institution_upload_method == "test":
        return update_satellite_from_satellite(
            upload_registry_sat,
            upload_status="processed",
            upload_message="Test upload was successful!",
        )
    if credit_institution_upload_method == "dkb":
        file_satellite = get_file_satellite_from_registry_satellite(upload_registry_sat)
        transactions = upload_dkb_transactions(
            account_hub,
            file_satellite.file.path,
        )
        return update_satellite_from_satellite(
            upload_registry_sat,
            upload_status="processed",
            upload_message=f"DKB upload was successful! (uploaded {len(transactions)} transactions)",
        )
    return update_satellite_from_satellite(
        upload_registry_sat,
        upload_status="failed",
        upload_message=f"Upload method {credit_institution_upload_method} not implemented",
    )


def _upload_file_to_registry(
    fileuploadregistrysat: FileUploadRegistryStaticSatellite,
    file: TextIO,
) -> FileUploadFileStaticSatellite:
    new_file_upload_file(fileuploadregistrysat, file)
    fileuploadregistry_uploaded = update_satellite_from_satellite(
        fileuploadregistrysat,
        upload_status="uploaded",
        upload_message=f"File {fileuploadregistrysat.file_name} has been uploaded",
    )
    return fileuploadregistry_uploaded


def _upload_error_file_not_uploaded_registry(upload_registry_sat):
    fileuploadregistry_failed = update_satellite_from_satellite(
        upload_registry_sat,
        upload_status="failed",
        upload_message=f"File {upload_registry_sat.file_name} has not been not uploaded",
    )
    return fileuploadregistry_failed


def _upload_error_account_upload_method_none(
    upload_registry_sat, credit_institution_name
):
    fileuploadregistry_failed = update_satellite_from_satellite(
        upload_registry_sat,
        upload_status="failed",
        upload_message=f"Credit Institution {credit_institution_name} provides no upload method",
    )
    return fileuploadregistry_failed
