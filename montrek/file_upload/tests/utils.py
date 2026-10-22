from baseclasses.repositories.montrek_repository import MontrekRepository
import pandas as pd
from typing import TYPE_CHECKING
from django.core.files.storage import default_storage
from django.test import TestCase
from storage.modules.local_storage_file import LocalStorageFile

if TYPE_CHECKING:
    # Lets mypy see the TestCase API the mixin uses; at runtime it stays a
    # plain mixin.
    _TestCaseBase = TestCase
else:
    _TestCaseBase = object


class LogFileTestMixin(_TestCaseBase):
    def assert_log_excel_file(
        self,
        registry_repository: MontrekRepository,
        err_msg: str,
        *,
        additional_data: pd.DataFrame = None,
        _startswith: bool = False,
    ):
        with LocalStorageFile(
            self._get_log_file_name(registry_repository)
        ) as log_excel_path:
            self._assert_log_excel_file(
                log_excel_path,
                err_msg,
                additional_data=additional_data,
                _startswith=_startswith,
            )

    def _assert_log_excel_file(
        self,
        log_excel_path: str,
        err_msg: str,
        *,
        additional_data: pd.DataFrame | None,
        _startswith: bool,
    ):
        test_excel_df = pd.read_excel(log_excel_path)
        result_msg = test_excel_df.set_index("Param").loc[
            "Upload Message", "Log Meta Data"
        ]
        if _startswith:
            self.assertTrue(result_msg.startswith(err_msg))
        else:
            self.assertEqual(
                result_msg,
                err_msg,
            )
        if additional_data is not None:
            result_aditional_data = pd.read_excel(
                log_excel_path, sheet_name="additional_data"
            ).fillna("")
            result_aditional_data = result_aditional_data.astype(str)
            additional_data = additional_data.astype(str)

            pd.testing.assert_frame_equal(
                result_aditional_data.reset_index(drop=True),
                additional_data.reset_index(drop=True),
                check_dtype=False,
            )

    def assert_log_txt_file(
        self,
        registry_repository: MontrekRepository,
        err_msg: str,
        *,
        additional_data: pd.DataFrame = None,
        _startswith: bool = False,
    ):
        log_txt_name = self._get_log_file_name(registry_repository)
        with default_storage.open(log_txt_name, "rb") as log_txt_file:
            file_content = log_txt_file.read().decode()
        self.assertIn(err_msg, file_content)
        if additional_data is not None:
            self.assertIn(additional_data.to_string(), file_content)

    def _get_log_file_name(self, registry_repository: MontrekRepository) -> str:
        upload_registry_query = registry_repository.receive()
        self.assertEqual(upload_registry_query.count(), 1)
        upload_registry = upload_registry_query.first()
        if upload_registry is None:
            self.fail("No upload registry entry found")
        return upload_registry.log_file
