from typing import List

from pydantic import BaseModel, ConfigDict


class ScanConfig(BaseModel):
    exclude_dirs: List[str] = []
    exlude_files: List[str] = []
    exclude_content_dirs: List[str] = []
    exlude_content_files: List[str] = []

    model_config = ConfigDict(from_attributes=True)
