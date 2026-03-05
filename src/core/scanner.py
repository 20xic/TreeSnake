import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from models import Directory, File, ScanConfig

from .file_reader import FileReader, IFileReader
from .rule import RuleSet

CONTENT_EXCLUDED = ""


@dataclass
class ScanContext:
    exclude_dirs: RuleSet
    exclude_files: RuleSet
    exclude_content_dirs: RuleSet
    exclude_content_files: RuleSet

    @classmethod
    def from_config(cls, config: ScanConfig) -> "ScanContext":
        return cls(
            exclude_dirs=RuleSet.from_patterns(config.exclude_dirs),
            exclude_files=RuleSet.from_patterns(config.exlude_files),
            exclude_content_dirs=RuleSet.from_patterns(config.exclude_content_dirs),
            exclude_content_files=RuleSet.from_patterns(config.exlude_content_files),
        )


class IScanner(ABC):
    @abstractmethod
    def scan(self, path: str, config: ScanConfig) -> Directory:
        raise NotImplementedError


class BaseScanner(IScanner):
    def __init__(self, file_reader: IFileReader | None = None):
        self._file_reader = file_reader or FileReader()

    def scan(self, path: str, config: ScanConfig) -> Directory:
        ctx = ScanContext.from_config(config)
        return self._scan_recursive(os.path.normpath(path), ctx)

    def _scan_recursive(self, path: str, ctx: ScanContext) -> Directory:
        try:
            items = os.listdir(path)
        except PermissionError:
            return Directory(name=os.path.basename(path), files=[], subdirectories=[])

        return Directory(
            name=os.path.basename(path),
            files=self._collect_files(path, items, ctx),
            subdirectories=self._collect_dirs(path, items, ctx),
        )

    def _collect_files(
        self, path: str, items: list[str], ctx: ScanContext
    ) -> list[File]:
        files = []
        for item in items:
            item_path = os.path.join(path, item)
            if not os.path.isfile(item_path):
                continue
            if ctx.exclude_files.matches(item):
                continue
            if ctx.exclude_content_files.matches(item):
                files.append(
                    File(
                        name=item,
                        content=CONTENT_EXCLUDED,
                        size=os.path.getsize(item_path),
                    )
                )
            else:
                files.append(self._file_reader.read(item_path))
        return files

    def _collect_dirs(
        self, path: str, items: list[str], ctx: ScanContext
    ) -> list[Directory]:
        subdirectories = []
        for item in items:
            item_path = os.path.join(path, item)
            if not os.path.isdir(item_path):
                continue
            if ctx.exclude_dirs.matches(item):
                continue
            if ctx.exclude_content_dirs.matches(item):
                subdirectories.append(Directory(name=item, files=[], subdirectories=[]))
            else:
                subdirectories.append(self._scan_recursive(item_path, ctx))
        return subdirectories
