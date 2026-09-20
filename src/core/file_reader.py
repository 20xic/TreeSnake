import os
from abc import ABC, abstractmethod

from models import File


class IFileReader(ABC):
    @abstractmethod
    def read(self, path: str, size: int | None = None) -> File:
        """Читает файл. `size` — уже известный размер (например, из
        `os.DirEntry.stat()`), чтобы не делать лишний stat; если None,
        размер запрашивается у ОС."""
        raise NotImplementedError


class FileReader(IFileReader):
    CONTENT_UNREADABLE = "[Content could not be read]"

    # Сколько байт смотреть на наличие NUL, прежде чем читать файл целиком.
    # Бинарники (.pyd, .dll, картинки) отсекаются по первому блоку, а не
    # после полного чтения и падения на UnicodeDecodeError.
    BINARY_SNIFF_BYTES = 8192

    def read(self, path: str, size: int | None = None) -> File:
        if size is None:
            size = os.path.getsize(path)

        try:
            with open(path, "rb") as f:
                head = f.read(self.BINARY_SNIFF_BYTES)
                if b"\0" in head:
                    content = self.CONTENT_UNREADABLE
                else:
                    content = self._normalize_newlines(
                        (head + f.read()).decode("utf-8")
                    )
        except (UnicodeDecodeError, OSError):
            content = self.CONTENT_UNREADABLE

        return File(name=os.path.basename(path), content=content, size=size)

    @staticmethod
    def _normalize_newlines(text: str) -> str:
        # То же, что делает текстовый режим open() (universal newlines):
        # \r\n и одиночный \r превращаются в \n.
        if "\r" not in text:
            return text
        return text.replace("\r\n", "\n").replace("\r", "\n")
