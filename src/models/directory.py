from dataclasses import dataclass, field

from .file import File


@dataclass(slots=True)
class Directory:
    name: str
    files: list[File] = field(default_factory=list)
    subdirectories: list["Directory"] = field(default_factory=list)
