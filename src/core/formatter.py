import json
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
import io

from models import Directory, File

T = TypeVar("T")


class IFormatter(ABC, Generic[T]):
    @abstractmethod
    def format(self, directory: Directory) -> T:
        raise NotImplementedError


class DefaultFormatter(IFormatter[str]):
    """Human-readable text with indentation."""

    def format(self, directory: Directory, prefix: str = "") -> str:
        buffer = io.StringIO()
        self._write(directory, prefix, buffer)
        return buffer.getvalue()

    def _write(self, directory: Directory, prefix: str, buffer: io.StringIO) -> None:
        buffer.write(f"{prefix}📁 {directory.name}/\n")

        items = [*directory.files, *directory.subdirectories]

        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")

            if isinstance(item, File):
                buffer.write(f"{prefix}{connector}📄 {item.name} ({item.size} bytes)\n")
                if item.content:
                    lines = item.content.splitlines()
                    for j, line in enumerate(lines):
                        is_last_line = j == len(lines) - 1
                        line_connector = "└── " if is_last_line else "│   "
                        buffer.write(f"{child_prefix}{line_connector}{line}\n")
            else:
                self._write(item, child_prefix, buffer)


class LLMFormatter(IFormatter[str]):
    """Token-efficient format for LLM consumption."""

    FILE_SEPARATOR = "---"

    def format(self, directory: Directory, _path: str = "") -> str:
        buffer = io.StringIO()
        self._write(directory, _path, buffer)
        return buffer.getvalue()

    def _write(self, directory: Directory, _path: str, buffer: io.StringIO) -> None:
        path = f"{_path}/{directory.name}" if _path else directory.name

        if not directory.files and not directory.subdirectories:
            buffer.write(f"# {path}/\n{self.FILE_SEPARATOR}\n")
            return

        for file in directory.files:
            file_path = f"{path}/{file.name}"
            buffer.write(f"# {file_path}\n")
            if file.content:
                buffer.write(file.content)
                buffer.write(f"\n{self.FILE_SEPARATOR}\n")
            else:
                buffer.write(f"{self.FILE_SEPARATOR}\n")

        for subdir in directory.subdirectories:
            self._write(subdir, path, buffer)


class JsonFormatter(IFormatter[dict]):
    """Returns a dictionary."""

    def format(self, directory: Directory) -> dict:
        return {
            "name": directory.name,
            "files": [
                {"name": f.name, "content": f.content, "size": f.size}
                for f in directory.files
            ],
            "subdirectories": [
                self.format(subdir) for subdir in directory.subdirectories
            ],
        }


class JsonStringFormatter(IFormatter[str]):
    """Returns a JSON string."""

    def __init__(self, indent: int | None = 2):
        self._indent = indent
        self._json_formatter = JsonFormatter()

    def format(self, directory: Directory) -> str:
        return json.dumps(
            self._json_formatter.format(directory),
            indent=self._indent,
            ensure_ascii=False,
        )
