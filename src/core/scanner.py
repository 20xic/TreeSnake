import os
from abc import ABC, abstractmethod

from models import Directory, File, ScanConfig, ScanResult, ScanTimer
from models.scan_config import CompiledRules

from .file_reader import FileReader, IFileReader

CONTENT_EXCLUDED = ""


def _too_large_placeholder(size: int) -> str:
    return f"[File too large: {size} bytes]"


class IScanner(ABC):
    @abstractmethod
    def scan(self, path: str, config: ScanConfig) -> ScanResult:
        raise NotImplementedError


class BaseScanner(IScanner):
    def __init__(self, file_reader: IFileReader | None = None):
        self._file_reader = file_reader or FileReader()

    def scan(self, path: str, config: ScanConfig) -> ScanResult:
        timer = ScanTimer()
        rules = config.compile()
        directory = self._scan_recursive(os.path.normpath(path), rules)
        elapsed = timer.stop()
        file_count, dir_count = self._count(directory)
        return ScanResult(
            directory=directory,
            elapsed=elapsed,
            file_count=file_count,
            dir_count=dir_count,
        )

    def _scan_recursive(self, path: str, rules: CompiledRules, depth: int = 0) -> Directory:
        name = os.path.basename(path)

        if rules.max_depth is not None and depth > rules.max_depth:
            return Directory(name=name, files=[], subdirectories=[])

        try:
            items = os.listdir(path)
        except PermissionError:
            return Directory(name=name, files=[], subdirectories=[])

        return Directory(
            name=name,
            files=self._collect_files(path, items, rules),
            subdirectories=self._collect_dirs(path, items, rules, depth),
        )

    def _collect_files(
        self, path: str, items: list[str], rules: CompiledRules
    ) -> list[File]:
        files = []
        for item in items:
            item_path = os.path.join(path, item)
            if not os.path.isfile(item_path):
                continue
            if rules.exclude_files.matches(item):
                continue
            if rules.include_files.rules and not rules.include_files.matches(item):
                continue

            size = os.path.getsize(item_path)

            if rules.exclude_content_files.matches(item):
                files.append(File(name=item, content=CONTENT_EXCLUDED, size=size))
            elif rules.max_file_size is not None and size > rules.max_file_size:
                files.append(
                    File(name=item, content=_too_large_placeholder(size), size=size)
                )
            else:
                files.append(self._file_reader.read(item_path))
        return files

    def _collect_dirs(
        self, path: str, items: list[str], rules: CompiledRules, depth: int
    ) -> list[Directory]:
        subdirectories = []
        for item in items:
            item_path = os.path.join(path, item)
            if not os.path.isdir(item_path):
                continue
            if rules.exclude_dirs.matches(item):
                continue
            if rules.include_dirs.rules and not rules.include_dirs.matches(item):
                continue
            if rules.exclude_content_dirs.matches(item):
                subdirectories.append(Directory(name=item, files=[], subdirectories=[]))
            else:
                subdirectories.append(self._scan_recursive(item_path, rules, depth + 1))
        return subdirectories

    def _count(self, directory: Directory) -> tuple[int, int]:
        file_count = len(directory.files)
        dir_count = len(directory.subdirectories)
        for subdir in directory.subdirectories:
            f, d = self._count(subdir)
            file_count += f
            dir_count += d
        return file_count, dir_count