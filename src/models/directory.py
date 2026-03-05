from typing import List

from pydantic import BaseModel

from .file import File


class Directory(BaseModel):
    name: str
    files: List[File]
    subdirectories: List["Directory"]
