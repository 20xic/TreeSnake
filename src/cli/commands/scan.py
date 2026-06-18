from pathlib import Path
from threading import Thread
from typing import Annotated, Optional

import typer
from rich.console import Console

from cli._version import __version__
from core.config_reader import ConfigReader
from core.scanner import BaseScanner
from core.update_checker import REQUEST_TIMEOUT_SECONDS, UpdateChecker
from models import ScanResult, ScanTimer
from models.scan_template import ScanTemplate

from ..types import OutputDest, OutputFormat
from ..utils import build_config, get_formatter, write_output


def _print_stats(
    result: ScanResult,
    format_elapsed: float,
    write_elapsed: float,
    total_elapsed: float,
    verbose: bool = False,
    console: Console | None = None,
) -> None:
    con = console or Console(stderr=True)
    total_ms = total_elapsed * 1000
    con.print(
        f"✔ Scanned [bold]{result.file_count}[/bold] files, "
        f"[bold]{result.dir_count}[/bold] dirs — "
        f"total [bold green]{total_ms:.1f}ms[/bold green]"
    )
    if verbose:

        def ms(seconds: float) -> str:
            return f"[bold green]{seconds * 1000:.1f}ms[/bold green]"

        con.print(
            f"   scan     {ms(result.elapsed)}\n"
            f"   format   {ms(format_elapsed)}\n"
            f"   write    {ms(write_elapsed)}"
        )


def _print_update_notice(
    update_checker: UpdateChecker,
    current_version: str,
    console: Console | None = None,
) -> None:
    if not update_checker.has_update():
        return
    con = console or Console(stderr=True)
    con.print(
        f"⚠ New version available: v{current_version} → v{update_checker.latest_version}\n"
        f"  {update_checker.release_url}",
        style="yellow",
    )


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
        Optional[list[str]],
        typer.Option("--exclude-dir", "-ed", help="Directory names to exclude. Repeatable."),
    ] = None,
    exclude_files: Annotated[
        Optional[list[str]],
        typer.Option("--exclude-file", "-ef", help="File names/patterns to exclude. Repeatable."),
    ] = None,
    exclude_content_dirs: Annotated[
        Optional[list[str]],
        typer.Option("--no-content-dir", "-ncd", help="Dirs to list without content. Repeatable."),
    ] = None,
    exclude_content_files: Annotated[
        Optional[list[str]],
        typer.Option("--no-content-file", "-ncf", help="Files to list without content. Repeatable."),
    ] = None,
    include_dirs: Annotated[
        Optional[list[str]],
        typer.Option(
            "--include-dir", "-id", help="Only include directories matching these names/patterns. Repeatable."
        ),
    ] = None,
    include_files: Annotated[
        Optional[list[str]],
        typer.Option(
            "--include-file", "-if", help="Only include files matching these names/patterns. Repeatable."
        ),
    ] = None,
    max_depth: Annotated[
        Optional[int],
        typer.Option("--max-depth", help="Limit recursion depth of the directory walk."),
    ] = None,
    max_file_size: Annotated[
        Optional[int],
        typer.Option(
            "--max-file-size",
            help="Files larger than this size (bytes) are listed with a placeholder instead of their content.",
        ),
    ] = None,
    only_tree: Annotated[
        bool,
        typer.Option(
            "--only-tree", help="Output only the directory structure, without file content."
        ),
    ] = False,
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
    stat: Annotated[
        bool,
        typer.Option("--stat", help="Show detailed timing breakdown."),
    ] = False,
) -> None:
    """Scan a directory tree and output its structure."""
    total_timer = ScanTimer()

    update_checker = UpdateChecker(__version__)
    update_thread = Thread(target=update_checker.check)
    update_thread.start()

    exclude_dirs = exclude_dirs or []
    exclude_files = exclude_files or []
    exclude_content_dirs = exclude_content_dirs or []
    exclude_content_files = exclude_content_files or []
    include_dirs = include_dirs or []
    include_files = include_files or []

    if only_tree:
        exclude_content_files = [*exclude_content_files, "*"]

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

    has_cli_overrides = any(
        [
            exclude_dirs,
            exclude_files,
            exclude_content_dirs,
            exclude_content_files,
            include_dirs,
            include_files,
            max_depth is not None,
            max_file_size is not None,
        ]
    )

    if has_cli_overrides:
        scan_config = build_config(
            exclude_dirs=list(exclude_dirs),
            exclude_files=list(exclude_files),
            exclude_content_dirs=list(exclude_content_dirs),
            exclude_content_files=list(exclude_content_files),
            include_dirs=list(include_dirs),
            include_files=list(include_files),
            max_depth=max_depth,
            max_file_size=max_file_size,
        )
    elif template is not None:
        scan_config = template.config
    else:
        scan_config = build_config([], [], [], [])

    resolved_fmt = fmt
    if resolved_fmt is None and template is not None:
        resolved_fmt = OutputFormat(template.mode)
    if resolved_fmt is None:
        resolved_fmt = OutputFormat.default

    resolved_output = output
    if resolved_output is None and template is not None:
        resolved_output = OutputDest(template.output)
    if resolved_output is None:
        resolved_output = OutputDest.stdout

    resolved_out_file = out_file
    if resolved_out_file is None and template is not None and template.out_file:
        resolved_out_file = Path(template.out_file)

    try:
        scan_result = BaseScanner().scan(str(path), scan_config)
    except OSError as exc:
        typer.echo(f"Scan failed: {exc}", err=True)
        raise typer.Exit(1)
    except Exception as exc:
        typer.echo(f"Unexpected error during scan: {exc}", err=True)
        raise typer.Exit(1)

    format_timer = ScanTimer()
    try:
        result = get_formatter(resolved_fmt).format(scan_result.directory)
    except Exception as exc:
        typer.echo(f"Failed to format output: {exc}", err=True)
        raise typer.Exit(1)
    format_elapsed = format_timer.stop()

    write_timer = ScanTimer()
    try:
        write_output(result, resolved_output, resolved_out_file)
    except OSError as exc:
        typer.echo(f"Failed to write output: {exc}", err=True)
        raise typer.Exit(1)
    write_elapsed = write_timer.stop()

    _print_stats(scan_result, format_elapsed, write_elapsed, total_timer.stop(), stat)

    update_thread.join(timeout=REQUEST_TIMEOUT_SECONDS)
    _print_update_notice(update_checker, __version__)