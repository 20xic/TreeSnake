from pathlib import Path
from typing import Optional

import typer

from core.clipboard import Clipboard
from core.formatter import DefaultFormatter, JsonStringFormatter, LLMFormatter
from core.gitignore_parser import GitignoreParser
from models import ScanConfig

from .types import OutputDest, OutputFormat


def get_formatter(fmt: OutputFormat):
    if fmt == OutputFormat.llm:
        return LLMFormatter()
    if fmt == OutputFormat.json:
        return JsonStringFormatter()
    return DefaultFormatter()


def write_output(text: str, dest: OutputDest, out_file: Optional[Path]) -> None:
    if dest == OutputDest.stdout:
        typer.echo(text)

    elif dest == OutputDest.clipboard:
        try:
            Clipboard().copy(text)
            typer.echo("Copied to clipboard.", err=True)
        except RuntimeError as exc:
            typer.echo(f"Clipboard error: {exc}", err=True)
            raise typer.Exit(1)

    elif dest == OutputDest.file:
        if out_file is None:
            typer.echo("--out-file is required when --output=file", err=True)
            raise typer.Exit(1)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(text, encoding="utf-8")
        typer.echo(f"Saved to {out_file}", err=True)


def _split_values(values: list[str]) -> list[str]:
    result = []
    for value in values:
        result.extend(value.split())
    return result


def build_config(
    exclude_dirs: list[str],
    exclude_files: list[str],
    exclude_content_dirs: list[str],
    exclude_content_files: list[str],
    include_dirs: Optional[list[str]] = None,
    include_files: Optional[list[str]] = None,
    max_depth: Optional[int] = None,
    max_file_size: Optional[int] = None,
) -> ScanConfig:
    return ScanConfig(
        exclude_dirs=_split_values(exclude_dirs),
        exclude_files=_split_values(exclude_files),
        exclude_content_dirs=_split_values(exclude_content_dirs),
        exclude_content_files=_split_values(exclude_content_files),
        include_dirs=_split_values(include_dirs or []),
        include_files=_split_values(include_files or []),
        max_depth=max_depth,
        max_file_size=max_file_size,
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