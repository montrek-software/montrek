"""Turn what a processor function returned into a file for the registry.

The builders take the ``data`` of a :class:`ProcessorReturn` and produce a
``ContentFile``, so a processor only has to decide which builder matches the
return type it declared.
"""

import os
from collections.abc import Callable
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
from django.core.files.base import ContentFile


def build_excel_file(
    sheets: dict[str, pd.DataFrame],
    file_name: str,
    formatter: Callable[..., None] | None = None,
) -> ContentFile:
    """Write one sheet per entry of *sheets*.

    *formatter* is called as ``formatter(writer, sheet_name=...)`` after each
    sheet is written, so callers can apply their own styling.
    """
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, data_frame in sheets.items():
            data_frame.to_excel(writer, sheet_name=sheet_name, index=False)
            if formatter is not None:
                formatter(writer, sheet_name=sheet_name)
    buffer.seek(0)
    return ContentFile(buffer.read(), name=file_name)


def build_zip_file(file_paths: list[str], file_name: str) -> ContentFile:
    """Zip the files at *file_paths*, flattening them to their base names.

    Raises ``ValueError`` when two paths share a base name: the archive would
    hold two members of the same name and extracting it would silently drop one
    of them, so the export would lose data.
    """
    arc_names = [os.path.basename(file_path) for file_path in file_paths]
    duplicates = sorted({name for name in arc_names if arc_names.count(name) > 1})
    if duplicates:
        raise ValueError(
            "Cannot build the archive: these file names occur more than once and "
            f"would overwrite each other on extraction: {', '.join(duplicates)}."
        )
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as zip_file:
        for file_path, arc_name in zip(file_paths, arc_names, strict=True):
            zip_file.write(file_path, arcname=arc_name)
    buffer.seek(0)
    return ContentFile(buffer.read(), name=file_name)


def build_bytes_file(data: bytes, file_name: str) -> ContentFile:
    """Wrap already rendered bytes, e.g. a PDF produced by a report manager."""
    return ContentFile(data, name=file_name)
