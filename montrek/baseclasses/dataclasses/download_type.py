from baseclasses.utils import ChoicesEnum


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
