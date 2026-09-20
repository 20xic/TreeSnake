import sys
from pathlib import Path

import typer

from core.clipboard import Clipboard
from core.formatter import (
    DefaultFormatter,
    IFormatter,
    JsonStringFormatter,
    LLMFormatter,
    XmlFormatter,
)
from core.gitignore_parser import GitignoreParser
from models import Directory, ScanConfig

from .types import OutputDest, OutputFormat


def get_formatter(fmt: OutputFormat) -> IFormatter:
    if fmt == OutputFormat.llm:
        return LLMFormatter()
    if fmt == OutputFormat.json:
        return JsonStringFormatter()
    if fmt == OutputFormat.xml:
        return XmlFormatter()
    return DefaultFormatter()


def write_output(
    formatter: IFormatter,
    directory: Directory,
    dest: OutputDest,
    out_file: Path | None,
) -> None:
    """Форматирует дерево прямо в место назначения. stdout и файл получают
    поток — итоговая строка целиком в памяти не собирается; буфер обмена
    по природе требует строку."""
    if dest == OutputDest.stdout:
        formatter.write(directory, sys.stdout)
        sys.stdout.flush()

    elif dest == OutputDest.clipboard:
        try:
            Clipboard().copy(formatter.format(directory))
            typer.echo("Copied to clipboard.", err=True)
        except RuntimeError as exc:
            typer.echo(f"Clipboard error: {exc}", err=True)
            raise typer.Exit(1) from exc

    elif dest == OutputDest.file:
        if out_file is None:
            typer.echo("--out-file is required when --output=file", err=True)
            raise typer.Exit(1)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            formatter.write(directory, f)
        typer.echo(f"Saved to {out_file}", err=True)


def _split_values(values: list[str]) -> list[str]:
    result = []
    for value in values:
        result.extend(value.split())
    return result


def build_config(**fields: list[str] | int | None) -> ScanConfig:
    """ScanConfig из CLI-значений. Списки дополнительно режутся по пробелам:
    `--exclude-dir ".git venv"` — то же, что два флага."""
    return ScanConfig(
        **{
            key: _split_values(value) if isinstance(value, list) else value
            for key, value in fields.items()
        }
    )


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def apply_gitignore(scan_config: ScanConfig, project_root: Path) -> ScanConfig:
    """Additively merges `<project_root>/.gitignore` patterns into
    exclude_dirs/exclude_files. Never removes anything the caller already
    set (via CLI flags or a config file) — only adds to it. Returns the
    same config unchanged if there's no .gitignore or it has no usable
    patterns."""
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.is_file():
        return scan_config

    patterns = GitignoreParser().parse(str(gitignore_path))
    if not patterns.dirs and not patterns.files:
        return scan_config

    return scan_config.model_copy(
        update={
            "exclude_dirs": _dedupe([*scan_config.exclude_dirs, *patterns.dirs]),
            "exclude_files": _dedupe([*scan_config.exclude_files, *patterns.files]),
        }
    )
