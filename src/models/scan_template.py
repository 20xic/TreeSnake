from typing import Literal

from pydantic import BaseModel

from .scan_config import ScanConfig


class ScanTemplate(BaseModel):
    config: ScanConfig
    mode: Literal["--json", "--llm", "--default", ""] = ""
    output: Literal["", "--clipboard", "--file"] = ""
    out_file: str | None = None