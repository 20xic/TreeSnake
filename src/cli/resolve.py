"""Сведение CLI-флагов и конфиг-файла в один набор параметров скана.

Чистые функции без Typer — правила приоритетов тестируются напрямую.

Приоритеты:
- фильтры (`exclude_*`/`include_*`/`max_*`) — всё или ничего: если задан
  хоть один CLI-фильтр, блок `config` из файла игнорируется целиком;
- `--only-tree` — не фильтр, а модификатор: добавляет `*` в
  `exclude_content_files` поверх того, что получилось;
- `--fmt`, `--output`, `--out-file`, `--gitignore` — каждый по отдельности
  переопределяет своё поле из файла;
- `.gitignore` затем добавляется поверх (аддитивно), если включён.
"""

from dataclasses import dataclass, field
from pathlib import Path

from models import ScanConfig
from models.scan_template import ScanTemplate

from .types import OutputDest, OutputFormat
from .utils import apply_gitignore, build_config


@dataclass(frozen=True)
class CliFilters:
    """Фильтры, пришедшие с командной строки (пустые списки = не заданы)."""

    exclude_dirs: list[str] = field(default_factory=list)
    exclude_files: list[str] = field(default_factory=list)
    exclude_content_dirs: list[str] = field(default_factory=list)
    exclude_content_files: list[str] = field(default_factory=list)
    include_dirs: list[str] = field(default_factory=list)
    include_files: list[str] = field(default_factory=list)
    max_depth: int | None = None
    max_file_size: int | None = None

    def any_set(self) -> bool:
        return bool(
            self.exclude_dirs
            or self.exclude_files
            or self.exclude_content_dirs
            or self.exclude_content_files
            or self.include_dirs
            or self.include_files
            or self.max_depth is not None
            or self.max_file_size is not None
        )

    def to_config(self) -> ScanConfig:
        return build_config(
            exclude_dirs=self.exclude_dirs,
            exclude_files=self.exclude_files,
            exclude_content_dirs=self.exclude_content_dirs,
            exclude_content_files=self.exclude_content_files,
            include_dirs=self.include_dirs,
            include_files=self.include_files,
            max_depth=self.max_depth,
            max_file_size=self.max_file_size,
        )


@dataclass(frozen=True)
class ScanOptions:
    scan_config: ScanConfig
    fmt: OutputFormat
    output: OutputDest
    out_file: Path | None


def resolve_scan_config(
    template: ScanTemplate | None,
    filters: CliFilters,
    *,
    only_tree: bool,
    use_gitignore: bool | None,
    project_root: Path,
) -> ScanConfig:
    if filters.any_set():
        scan_config = filters.to_config()
    elif template is not None:
        scan_config = template.config
    else:
        scan_config = ScanConfig()

    if only_tree:
        scan_config = scan_config.model_copy(
            update={"exclude_content_files": [*scan_config.exclude_content_files, "*"]}
        )

    if use_gitignore is None:
        use_gitignore = template.use_gitignore if template is not None else True
    if use_gitignore:
        scan_config = apply_gitignore(scan_config, project_root)

    return scan_config


def resolve_options(
    template: ScanTemplate | None,
    filters: CliFilters,
    *,
    only_tree: bool = False,
    use_gitignore: bool | None = None,
    fmt: OutputFormat | None = None,
    output: OutputDest | None = None,
    out_file: Path | None = None,
    project_root: Path,
) -> ScanOptions:
    scan_config = resolve_scan_config(
        template,
        filters,
        only_tree=only_tree,
        use_gitignore=use_gitignore,
        project_root=project_root,
    )

    if fmt is None:
        fmt = OutputFormat(template.mode) if template else OutputFormat.default
    if output is None:
        output = OutputDest(template.output) if template else OutputDest.stdout
    if out_file is None and template is not None and template.out_file:
        out_file = Path(template.out_file)

    return ScanOptions(
        scan_config=scan_config, fmt=fmt, output=output, out_file=out_file
    )
