from enum import Enum

from core.config_format import ConfigFormat

__all__ = ["ConfigFormat", "OutputDest", "OutputFormat"]


class OutputFormat(str, Enum):
    default = "default"
    llm = "llm"
    json = "json"
    xml = "xml"


class OutputDest(str, Enum):
    stdout = "stdout"
    file = "file"
    clipboard = "clipboard"
