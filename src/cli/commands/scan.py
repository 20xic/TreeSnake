from pathlib import Path
from typing import Annotated, Optional

import typer

from core.config_reader import ConfigReader
from core.scanner import BaseScanner
from models.scan_template import ScanTemplate

from ..types import OutputDest, OutputFormat
from ..utils import build_config, get_formatter, write_output

_MODE_TO_FORMAT = {
    "--llm": OutputFormat.llm,
    "--json": OutputFormat.json,
    "--default": OutputFormat.default,
    "": OutputFormat.default,
}

_OUTPUT_TO_DEST = {
    "--buffer": OutputDest.clipboard,
    "--file": OutputDest.file,
    "": OutputDest.stdout,
}


def scan(
    path: Annotated[
        Path,
        typer.Argument(help="Directory to scan."),
    ] = Path("."),
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-c",
            help="Path to a config file (.env / .json / .yml / .toml). "
            "CLI options override values from the config.",
        ),
    ] = None,
    exclude_dirs: Annotated[
        list[str],
        typer.Option(
            "--exclude-dir", "-ed", help="Directory names to exclude. Repeatable."
        ),
    ] = [],
    exclude_files: Annotated[
        list[str],
        typer.Option(
            "--exclude-file", "-ef", help="File names/patterns to exclude. Repeatable."
        ),
    ] = [],
    exclude_content_dirs: Annotated[
        list[str],
        typer.Option(
            "--no-content-dir", "-ncd", help="Dirs to list without content. Repeatable."
        ),
    ] = [],
    exclude_content_files: Annotated[
        list[str],
        typer.Option(
            "--no-content-file",
            "-ncf",
            help="Files to list without content. Repeatable.",
        ),
    ] = [],
    fmt: Annotated[
        Optional[OutputFormat],
        typer.Option("--fmt", "-f", help="Output format. Overrides config."),
    ] = None,
    output: Annotated[
        Optional[OutputDest],
        typer.Option(
            "--output", "-o", help="Where to send the result. Overrides config."
        ),
    ] = None,
    out_file: Annotated[
        Optional[Path],
        typer.Option(
            "--out-file", help="Output file path (required when --output=file)."
        ),
    ] = None,
) -> None:
    """Scan a directory tree and output its structure."""
    path = path.resolve()

    if not path.exists() or not path.is_dir():
        typer.echo(f"Path does not exist or is not a directory: {path}", err=True)
        raise typer.Exit(1)

    template: Optional[ScanTemplate] = None

    if config is not None:
        config = config.resolve()
        if not config.exists():
            typer.echo(f"Config file not found: {config}", err=True)
            raise typer.Exit(1)
        try:
            template = ConfigReader().read(str(config))
        except Exception as exc:
            typer.echo(f"Failed to read config: {exc}", err=True)
            raise typer.Exit(1)

    if any([exclude_dirs, exclude_files, exclude_content_dirs, exclude_content_files]):
        scan_config = build_config(
            exclude_dirs=list(exclude_dirs),
            exclude_files=list(exclude_files),
            exclude_content_dirs=list(exclude_content_dirs),
            exclude_content_files=list(exclude_content_files),
        )
    elif template is not None:
        scan_config = template.config
    else:
        scan_config = build_config([], [], [], [])

    resolved_fmt = fmt
    if resolved_fmt is None and template is not None:
        resolved_fmt = _MODE_TO_FORMAT.get(template.mode, OutputFormat.default)
    if resolved_fmt is None:
        resolved_fmt = OutputFormat.default

    resolved_output = output
    if resolved_output is None and template is not None:
        resolved_output = _OUTPUT_TO_DEST.get(template.output, OutputDest.stdout)
    if resolved_output is None:
        resolved_output = OutputDest.stdout

    resolved_out_file = out_file
    if resolved_out_file is None and template is not None and template.out_file:
        resolved_out_file = Path(template.out_file)

    directory = BaseScanner().scan(str(path), scan_config)
    result = get_formatter(resolved_fmt).format(directory)
    write_output(result, resolved_output, resolved_out_file)
