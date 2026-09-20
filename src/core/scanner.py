import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

from models import Directory, File, ScanConfig, ScanResult, ScanTimer

from .file_reader import FileReader, IFileReader
from .rule import CompiledRules

CONTENT_EXCLUDED = ""

# Чтение файлов — I/O, GIL на время open/read отпускается, поэтому пул потоков
# даёт кратный выигрыш на холодном кэше и SSD. Значение как у stdlib-дефолта
# ThreadPoolExecutor; больше — нет смысла, упираемся в диск.
DEFAULT_WORKERS = min(32, (os.cpu_count() or 1) + 4)


def _too_large_placeholder(size: int) -> str:
    return f"[File too large: {size} bytes]"


class IScanner(ABC):
    @abstractmethod
    def scan(self, path: str, config: ScanConfig) -> ScanResult:
        raise NotImplementedError


class BaseScanner(IScanner):
    """Сканирует в два прохода: сначала обход дерева (структура, размеры,
    фильтры) — файлы, чьё содержимое нужно прочитать, откладываются;
    затем их содержимое читается пулом потоков. Порядок файлов в дереве
    от этого не зависит — он фиксируется на первом проходе.

    `workers=1` (или 0) читает последовательно — удобно для тестов
    с моками и отладки."""

    def __init__(
        self,
        file_reader: IFileReader | None = None,
        workers: int = DEFAULT_WORKERS,
    ):
        self._file_reader = file_reader or FileReader()
        self._workers = max(1, workers)
        # (File-заглушка в дереве, путь, размер) — заполняется на обходе
        self._pending: list[tuple[File, str, int]] = []

    def scan(self, path: str, config: ScanConfig) -> ScanResult:
        timer = ScanTimer()
        rules = CompiledRules.from_config(config)
        self._pending = []
        directory = self._scan_recursive(os.path.normpath(path), rules)
        self._read_pending()
        elapsed = timer.stop()
        file_count, dir_count = self._count(directory)
        return ScanResult(
            directory=directory,
            elapsed=elapsed,
            file_count=file_count,
            dir_count=dir_count,
        )

    def _scan_recursive(
        self, path: str, rules: CompiledRules, depth: int = 0
    ) -> Directory:
        name = os.path.basename(path)

        if rules.max_depth is not None and depth > rules.max_depth:
            return Directory(name=name)

        # Один проход scandir вместо listdir + isfile + isdir + getsize на каждый
        # элемент: DirEntry отдаёт тип (и на Windows — stat) из результата
        # листинга без дополнительных syscall'ов. Сортируем по имени, чтобы
        # вывод не зависел от порядка, в котором ФС отдаёт элементы (ext4 —
        # произвольный, NTFS — алфавитный).
        try:
            with os.scandir(path) as it:
                entries = sorted(it, key=lambda e: e.name)
        except PermissionError:
            return Directory(name=name)

        files: list[File] = []
        subdirectories: list[Directory] = []
        for entry in entries:
            if entry.is_file():
                file = self._collect_file(entry, rules)
                if file is not None:
                    files.append(file)
            elif entry.is_dir():
                subdir = self._collect_dir(entry, rules, depth)
                if subdir is not None:
                    subdirectories.append(subdir)

        return Directory(name=name, files=files, subdirectories=subdirectories)

    def _collect_file(self, entry: os.DirEntry, rules: CompiledRules) -> File | None:
        name = entry.name
        if rules.exclude_files.matches(name):
            return None
        if rules.include_files.rules and not rules.include_files.matches(name):
            return None

        size = entry.stat().st_size

        if rules.exclude_content_files.matches(name):
            return File(name=name, content=CONTENT_EXCLUDED, size=size)
        if rules.max_file_size is not None and size > rules.max_file_size:
            return File(name=name, content=_too_large_placeholder(size), size=size)

        file = File(name=name, content="", size=size)
        self._pending.append((file, entry.path, size))
        return file

    def _read_pending(self) -> None:
        pending, self._pending = self._pending, []
        if not pending:
            return

        def read(item: tuple[File, str, int]) -> str:
            _, path, size = item
            return self._file_reader.read(path, size).content

        if self._workers == 1 or len(pending) == 1:
            contents = map(read, pending)
        else:
            workers = min(self._workers, len(pending))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                contents = pool.map(read, pending)

        for (file, _, _), content in zip(pending, contents, strict=True):
            file.content = content

    def _collect_dir(
        self, entry: os.DirEntry, rules: CompiledRules, depth: int
    ) -> Directory | None:
        name = entry.name
        if rules.exclude_dirs.matches(name):
            return None
        if rules.include_dirs.rules and not rules.include_dirs.matches(name):
            return None
        if rules.exclude_content_dirs.matches(name):
            return Directory(name=name)
        return self._scan_recursive(entry.path, rules, depth + 1)

    def _count(self, directory: Directory) -> tuple[int, int]:
        file_count = len(directory.files)
        dir_count = len(directory.subdirectories)
        for subdir in directory.subdirectories:
            f, d = self._count(subdir)
            file_count += f
            dir_count += d
        return file_count, dir_count
