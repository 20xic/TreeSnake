import io
import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TextIO
from xml.sax.saxutils import quoteattr

from models import Directory, File


def walk(directory: Directory) -> Iterator[tuple[str, Directory]]:
    """Обход дерева в pre-order: (путь_от_корня, директория).
    Путь — имена через `/`, корень идёт под своим именем."""
    stack = [(directory.name, directory)]
    while stack:
        path, current = stack.pop()
        yield path, current
        # push в обратном порядке, чтобы pop отдавал поддиректории по порядку
        stack.extend(
            (f"{path}/{sub.name}", sub) for sub in reversed(current.subdirectories)
        )


class IFormatter(ABC):
    """Форматтер пишет дерево в поток. `format()` — удобная обёртка,
    когда нужна строка (например, для буфера обмена); для stdout и файла
    вызывайте `write()` напрямую, чтобы не держать весь вывод в памяти."""

    @abstractmethod
    def write(self, directory: Directory, stream: TextIO) -> None:
        raise NotImplementedError

    def format(self, directory: Directory) -> str:
        buffer = io.StringIO()
        self.write(directory, buffer)
        return buffer.getvalue()


class DefaultFormatter(IFormatter):
    """Human-readable text with indentation."""

    def write(self, directory: Directory, stream: TextIO) -> None:
        self._write_dir(directory, "", stream)

    def _write_dir(self, directory: Directory, prefix: str, stream: TextIO) -> None:
        stream.write(f"{prefix}📁 {directory.name}/\n")

        items: list[File | Directory] = [*directory.files, *directory.subdirectories]
        last_index = len(items) - 1

        for i, item in enumerate(items):
            is_last = i == last_index
            connector = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")

            if isinstance(item, File):
                stream.write(f"{prefix}{connector}📄 {item.name} ({item.size} bytes)\n")
                if item.content:
                    self._write_content(item.content, child_prefix, stream)
            else:
                self._write_dir(item, child_prefix, stream)

    @staticmethod
    def _write_content(content: str, prefix: str, stream: TextIO) -> None:
        lines = content.splitlines()
        body, last = lines[:-1], lines[-1]
        if body:
            branch = f"\n{prefix}│   "
            stream.write(f"{prefix}│   {branch.join(body)}\n")
        stream.write(f"{prefix}└── {last}\n")


class LLMFormatter(IFormatter):
    """Token-efficient format for LLM consumption."""

    FILE_SEPARATOR = "---"

    def write(self, directory: Directory, stream: TextIO) -> None:
        for path, current in walk(directory):
            if not current.files and not current.subdirectories:
                stream.write(f"# {path}/\n{self.FILE_SEPARATOR}\n")
                continue

            for file in current.files:
                stream.write(f"# {path}/{file.name}\n")
                if file.content:
                    stream.write(file.content)
                    stream.write("\n")
                stream.write(f"{self.FILE_SEPARATOR}\n")


class XmlFormatter(IFormatter):
    """Nested XML tree for LLM consumption.

    Directories nest as <directory> elements so the hierarchy is explicit
    in the markup itself; every <file> additionally carries its full
    `path` so a model can reference a file without re-walking the tree.
    File content is wrapped in CDATA rather than entity-escaped: code
    full of `&lt;`/`&amp;` is harder for a model to read than the raw
    source, and CDATA keeps it verbatim. The only sequence CDATA can't
    contain is its own terminator, so `]]>` inside content is split
    across two CDATA sections.
    """

    INDENT = "  "

    def write(self, directory: Directory, stream: TextIO) -> None:
        stream.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self._write_dir(directory, directory.name, 0, stream, tag="project")

    def _write_dir(
        self,
        directory: Directory,
        path: str,
        depth: int,
        stream: TextIO,
        tag: str = "directory",
    ) -> None:
        indent = self.INDENT * depth
        if not directory.files and not directory.subdirectories:
            stream.write(f"{indent}<{tag} name={quoteattr(directory.name)} />\n")
            return

        stream.write(f"{indent}<{tag} name={quoteattr(directory.name)}>\n")
        for file in directory.files:
            self._write_file(file, f"{path}/{file.name}", depth + 1, stream)
        for subdir in directory.subdirectories:
            self._write_dir(subdir, f"{path}/{subdir.name}", depth + 1, stream)
        stream.write(f"{indent}</{tag}>\n")

    def _write_file(self, file: File, path: str, depth: int, stream: TextIO) -> None:
        indent = self.INDENT * depth
        attrs = f'name={quoteattr(file.name)} path={quoteattr(path)} size="{file.size}"'
        if not file.content:
            stream.write(f"{indent}<file {attrs} />\n")
            return

        stream.write(f"{indent}<file {attrs}><![CDATA[\n")
        stream.write(file.content.replace("]]>", "]]]]><![CDATA[>"))
        if not file.content.endswith("\n"):
            stream.write("\n")
        stream.write("]]></file>\n")


class JsonFormatter:
    """Дерево -> dict (та же структура, что у Directory)."""

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


class JsonStringFormatter(IFormatter):
    """Дерево -> JSON-текст."""

    def __init__(self, indent: int | None = 2):
        self._indent = indent
        self._json_formatter = JsonFormatter()

    def write(self, directory: Directory, stream: TextIO) -> None:
        json.dump(
            self._json_formatter.format(directory),
            stream,
            indent=self._indent,
            ensure_ascii=False,
        )
        stream.write("\n")
