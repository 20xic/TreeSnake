from pathlib import Path
from typing import Optional

import typer

from core.clipboard import Clipboard
from core.formatter import DefaultFormatter, JsonStringFormatter, LLMFormatter
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
) -> ScanConfig:
    return ScanConfig(
        exclude_dirs=_split_values(exclude_dirs),
        exclude_files=_split_values(exclude_files),
        exclude_content_dirs=_split_values(exclude_content_dirs),
        exclude_content_files=_split_values(exclude_content_files),
    )
