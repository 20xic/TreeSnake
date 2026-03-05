import os
from abc import ABC, abstractmethod

from models import File


class IFileReader(ABC):
    @abstractmethod
    def read(self, path: str) -> File:
        raise NotImplementedError


class FileReader(IFileReader):
    CONTENT_UNREADABLE = "[Content could not be read]"

    def read(self, path: str) -> File:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError, OSError):
            content = self.CONTENT_UNREADABLE

        return File(
            name=os.path.basename(path),
            content=content,
            size=os.path.getsize(path),
        )
