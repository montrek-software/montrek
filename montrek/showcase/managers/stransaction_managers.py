import logging
import pandas as pd
from file_upload.managers.background_file_upload_manager import (
    BackgroundFileUploadManagerABC,
)
from file_upload.managers.file_upload_manager import FileUploadManagerABC
from file_upload.managers.file_upload_registry_manager import (
    FileUploadRegistryManagerABC,
)
from file_upload.models import FileUploadRegistryHubABC
from file_upload.tasks.process_file_task import ProcessFileTaskABC
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.repositories.sasset_repositories import SAssetRepository
from showcase.repositories.sproduct_repositories import SProductRepository
from showcase.repositories.stransaction_repositories import (
    SProductSPositionRepository,
    SProductSTransactionRepository,
    STransactionFURegistryRepository,
    STransactionRepository,
)

logger = logging.getLogger(__file__)


class STransactionTableManager(MontrekTableManager):
    repository_class = STransactionRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Product Name", attr="product_name"),
            te.StringTableElement(name="Asset Name", attr="asset_name"),
            te.DateTableElement(name="Transaction Date", attr="transaction_date"),
            te.StringTableElement(
                name="Transaction External Identifier",
                attr="transaction_external_identifier",
            ),
            te.StringTableElement(
                name="Transaction Description", attr="transaction_description"
            ),
            te.FloatTableElement(
                name="Transaction Quantity", attr="transaction_quantity"
            ),
            te.MoneyTableElement(name="Transaction Price", attr="transaction_price"),
            te.LinkTableElement(
                name="Edit",
                url="stransaction_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Transaction",
            ),
            te.LinkTableElement(
                name="Delete",
                url="stransaction_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Transaction",
            ),
        ]


class SProductSTransactionTableManager(STransactionTableManager):
    repository_class = SProductSTransactionRepository


class SProductSPositionTableManager(MontrekTableManager):
    repository_class = SProductSPositionRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Asset Name", attr="asset_name"),
            te.StringTableElement(name="Asset ISIN", attr="asset_isin"),
            te.FloatTableElement(name="Position Quantity", attr="position_quantity"),
        ]


class STransactionFURegistryManager(FileUploadRegistryManagerABC):
    repository_class = STransactionFURegistryRepository
    download_url = "stransaction_download_file"


class STransactionFUProcessor:
    message = ""

    def __init__(
        self,
        file_upload_registry_hub: FileUploadRegistryHubABC,
        session_data: dict,
        **kwargs,
    ):
        self.session_data = session_data

    @staticmethod
    def _log_start(description: str):
        logger.info(f"START: {description}")

    @staticmethod
    def _log_end(description: str):
        logger.info(f"END: {description}")

    def pre_check(self, file_path: str) -> bool:
        return True

    def process(self, file_path: str) -> bool:
        self._log_start("reading_file")
        input_df = pd.read_csv(file_path)
        self._log_end("reading_file")
        transaction_df = input_df[
            [
                "transaction_date",
                "transaction_external_identifier",
                "transaction_description",
                "transaction_quantity",
                "transaction_price",
            ]
        ]
        transaction_repo = STransactionRepository(self.session_data)
        self._log_start("creating transactions")
        transaction_repo.create_objects_from_data_frame(transaction_df)
        self._log_end("creating transactions")

        self._log_start("adding transaction hub entity ids")
        transaction_hubs = transaction_repo.get_hubs_by_field_values(
            values=transaction_df["transaction_external_identifier"].tolist(),
            by_repository_field="transaction_external_identifier",
        )
        transaction_df["hub_entity_id"] = [h.id for h in transaction_hubs]
        self._log_end("adding transaction hub entity ids")

        self._log_start("creating links")
        link_df = transaction_df[["hub_entity_id"]]
        asset_repo = SAssetRepository(self.session_data)
        link_df["link_stransaction_sasset"] = asset_repo.get_hubs_by_field_values(
            values=input_df["ISIN"],
            by_repository_field="asset_isin",
        )
        product_repo = SProductRepository(self.session_data)
        link_df["link_stransaction_sproduct"] = product_repo.get_hubs_by_field_values(
            values=input_df["product_name"],
            by_repository_field="product_name",
        )
        transaction_repo.create_objects_from_data_frame(link_df)
        self._log_end("creating links")
        self.message = f"Successfully processed {len(transaction_df)} transactions"
        return True

    def post_check(self, file_path: str) -> bool:
        return True


class STransactionFUManager(FileUploadManagerABC):
    file_upload_processor_class = STransactionFUProcessor
    file_registry_manager_class = STransactionFURegistryManager


class STransactionProcessFileTask(ProcessFileTaskABC):
    file_upload_processor_class = STransactionFUProcessor
    file_upload_registry_repository_class = STransactionFURegistryRepository


class STransactionBFUManager(BackgroundFileUploadManagerABC):
    file_upload_processor_class = STransactionFUProcessor
    file_registry_manager_class = STransactionFURegistryManager
    task = STransactionProcessFileTask()
