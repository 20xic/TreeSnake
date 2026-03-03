from typing import List

from pydantic import BaseModel

from .file import File


class Directory(BaseModel):
    name: str
    subdirectories: List["Directory"] = []
    files: List[File] = []
    skip_content: bool = False

    class Config:
        arbitrary_types_allowed = True
