import json
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from models import Directory, File

T = TypeVar("T")


class IFormatter(ABC, Generic[T]):
    @abstractmethod
    def format(self, directory: Directory) -> T:
        raise NotImplementedError


class DefaultFormatter(IFormatter[str]):
    """Human-readable text with indentation."""

    def format(self, directory: Directory, prefix: str = "") -> str:
        lines = [f"{prefix}📁 {directory.name}/"]

        items = [*directory.files, *directory.subdirectories]

        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")

            if isinstance(item, File):
                lines.append(f"{prefix}{connector}📄 {item.name} ({item.size} bytes)")
                if item.content:
                    for j, line in enumerate(item.content.splitlines()):
                        is_last_line = j == len(item.content.splitlines()) - 1
                        line_connector = "└── " if is_last_line else "│   "
                        lines.append(f"{child_prefix}{line_connector}{line}")
            else:
                lines.append(
                    self.format(item, child_prefix).replace(
                        f"{child_prefix}📁", f"{prefix}{connector}📁", 1
                    )
                )

        return "\n".join(lines)


class LLMFormatter(IFormatter[str]):
    """Token-efficient format for LLM consumption."""

    FILE_SEPARATOR = "---"

    def format(self, directory: Directory, _path: str = "") -> str:
        path = f"{_path}/{directory.name}" if _path else directory.name
        blocks = []

        for file in directory.files:
            file_path = f"{path}/{file.name}"
            if file.content:
                blocks.append(f"# {file_path}\n{file.content}\n{self.FILE_SEPARATOR}")
            else:
                blocks.append(f"# {file_path}\n{self.FILE_SEPARATOR}")

        for subdir in directory.subdirectories:
            blocks.append(self.format(subdir, path))

        return "\n".join(blocks)


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
