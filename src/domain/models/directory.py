from dataclasses import dataclass
from typing import List
from src.domain.models.file import File


@dataclass
class Directory:
    name: str
    subdirectories: List["Directory"]
    files: List[File]
    skip_content: bool = False