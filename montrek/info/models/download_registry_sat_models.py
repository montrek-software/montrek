from django.db import models

from baseclasses.models import MontrekSatelliteABC
from baseclasses.utils import ChoicesEnum
from info.models.download_registry_hub_models import DownloadRegistryHub


class DownloadType(ChoicesEnum):
    # Spreadsheets / tabular
    XLSX = "xlsx"
    XLS = "xls"
    CSV = "csv"
    TSV = "tsv"
    ODS = "ods"

    # Documents
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    MD = "md"
    RTF = "rtf"
    HTML = "html"

    # Data / structured
    JSON = "json"
    XML = "xml"
    YAML = "yaml"
    YML = "yml"
    PARQUET = "parquet"
    AVRO = "avro"
    TOML = "toml"

    # Archives
    ZIP = "zip"
    TAR = "tar"
    GZ = "gz"
    TGZ = "tgz"
    SEVEN_Z = "7z"

    # Media (often exported)
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    SVG = "svg"
    MP3 = "mp3"
    MP4 = "mp4"

    # Interfaces / special
    API = "api"
    MD = "md"



class DownloadRegistrySatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(DownloadRegistryHub, on_delete=models.CASCADE)

    download_name = models.CharField()
    download_type = models.CharField(max_length=25, choices=DownloadType.to_list())

    identifier_fields = ["hub_entity_id"]
