from typing import Literal

from pydantic import BaseModel

from .scan_config import ScanConfig


class ScanTemplate(BaseModel):
    config: ScanConfig
    mode: Literal["default", "llm", "json"] = "default"
    output: Literal["stdout", "clipboard", "file"] = "stdout"
    out_file: str | None = None
