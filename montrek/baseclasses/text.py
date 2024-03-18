import re


def clean_column_name(column_name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", column_name.strip().lower()).strip("_")
