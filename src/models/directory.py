from pydantic import BaseModel

from .file import File


class Directory(BaseModel):
    name: str
    files: list[File]
    subdirectories: list["Directory"]
