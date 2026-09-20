from pathlib import Path
from threading import Thread
from typing import Annotated

import typer
from rich.console import Console

from cli._version import __version__
from core.config_discovery import ConfigDiscovery
from core.config_reader import ConfigReader
from core.scanner import BaseScanner
from core.update_checker import REQUEST_TIMEOUT_SECONDS, UpdateChecker
from models import ScanResult, ScanTimer
from models.scan_template import ScanTemplate

from ..resolve import CliFilters, ScanOptions, resolve_options
from ..types import OutputDest, OutputFormat
from ..utils import get_formatter, write_output


def _print_stats(
    result: ScanResult,
    output_elapsed: float,
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
            f"   output   {ms(output_elapsed)}  (format + write)"
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


def load_template(config: Path | None, project_root: Path) -> ScanTemplate | None:
    """Явный `--config` обязан прочитаться (иначе выход с ошибкой);
    автоматически найденный — лишь предупреждение, скан идёт с дефолтами."""
    if config is not None:
        config = config.resolve()
        if not config.exists():
            typer.echo(f"Config file not found: {config}", err=True)
            raise typer.Exit(1)
        try:
            return ConfigReader().read(str(config))
        except Exception as exc:
            typer.echo(f"Failed to read config: {exc}", err=True)
            raise typer.Exit(1) from exc

    discovered = ConfigDiscovery().find(str(project_root))
    if discovered is None:
        return None
    try:
        return ConfigReader().read(discovered)
    except Exception as exc:
        typer.echo(f"Warning: ignoring discovered config {discovered}: {exc}", err=True)
        return None


def run_pipeline(path: Path, options: ScanOptions) -> tuple[ScanResult, float]:
    """scan -> format -> write. Возвращает результат скана и время вывода."""
    try:
        scan_result = BaseScanner().scan(str(path), options.scan_config)
    except OSError as exc:
        typer.echo(f"Scan failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    except Exception as exc:
        typer.echo(f"Unexpected error during scan: {exc}", err=True)
        raise typer.Exit(1) from exc

    output_timer = ScanTimer()
    try:
        write_output(
            get_formatter(options.fmt),
            scan_result.directory,
            options.output,
            options.out_file,
        )
    except typer.Exit:
        raise
    except OSError as exc:
        typer.echo(f"Failed to write output: {exc}", err=True)
        raise typer.Exit(1) from exc
    except Exception as exc:
        typer.echo(f"Failed to format output: {exc}", err=True)
        raise typer.Exit(1) from exc
    return scan_result, output_timer.stop()


def scan(
    path: Annotated[
        Path,
        typer.Argument(help="Directory to scan."),
    ] = Path("."),
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to a config file (.env / .json / .yml / .toml). "
            "CLI options override values from the config.",
        ),
    ] = None,
    exclude_dirs: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude-dir", "-ed", help="Directory names to exclude. Repeatable."
        ),
    ] = None,
    exclude_files: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude-file", "-ef", help="File names/patterns to exclude. Repeatable."
        ),
    ] = None,
    exclude_content_dirs: Annotated[
        list[str] | None,
        typer.Option(
            "--no-content-dir", "-ncd", help="Dirs to list without content. Repeatable."
        ),
    ] = None,
    exclude_content_files: Annotated[
        list[str] | None,
        typer.Option(
            "--no-content-file",
            "-ncf",
            help="Files to list without content. Repeatable.",
        ),
    ] = None,
    include_dirs: Annotated[
        list[str] | None,
        typer.Option(
            "--include-dir",
            "-id",
            help="Only include directories matching these names/patterns. Repeatable.",
        ),
    ] = None,
    include_files: Annotated[
        list[str] | None,
        typer.Option(
            "--include-file",
            "-if",
            help="Only include files matching these names/patterns. Repeatable.",
        ),
    ] = None,
    max_depth: Annotated[
        int | None,
        typer.Option(
            "--max-depth", help="Limit recursion depth of the directory walk."
        ),
    ] = None,
    max_file_size: Annotated[
        int | None,
        typer.Option(
            "--max-file-size",
            help="Files larger than this size (bytes) are listed with a placeholder instead of their content.",
        ),
    ] = None,
    only_tree: Annotated[
        bool,
        typer.Option(
            "--only-tree",
            help="Output only the directory structure, without file content.",
        ),
    ] = False,
    use_gitignore: Annotated[
        bool | None,
        typer.Option(
            "--gitignore/--no-gitignore",
            help=(
                "Automatically exclude patterns from the project's .gitignore "
                "(merged additively with --exclude-dir/--exclude-file and any "
                "config file — nothing you've explicitly excluded gets un-excluded). "
                "Overrides the config file's use_gitignore if set there; "
                "defaults to enabled when neither specifies it."
            ),
        ),
    ] = None,
    fmt: Annotated[
        OutputFormat | None,
        typer.Option("--fmt", "-f", help="Output format. Overrides config."),
    ] = None,
    output: Annotated[
        OutputDest | None,
        typer.Option(
            "--output", "-o", help="Where to send the result. Overrides config."
        ),
    ] = None,
    out_file: Annotated[
        Path | None,
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

    path = path.resolve()
    if not path.exists() or not path.is_dir():
        typer.echo(f"Path does not exist or is not a directory: {path}", err=True)
        raise typer.Exit(1)

    template = load_template(config, path)
    options = resolve_options(
        template,
        CliFilters(
            exclude_dirs=exclude_dirs or [],
            exclude_files=exclude_files or [],
            exclude_content_dirs=exclude_content_dirs or [],
            exclude_content_files=exclude_content_files or [],
            include_dirs=include_dirs or [],
            include_files=include_files or [],
            max_depth=max_depth,
            max_file_size=max_file_size,
        ),
        only_tree=only_tree,
        use_gitignore=use_gitignore,
        fmt=fmt,
        output=output,
        out_file=out_file,
        project_root=path,
    )

    scan_result, output_elapsed = run_pipeline(path, options)

    _print_stats(scan_result, output_elapsed, total_timer.stop(), stat)

    update_thread.join(timeout=REQUEST_TIMEOUT_SECONDS)
    _print_update_notice(update_checker, __version__)
