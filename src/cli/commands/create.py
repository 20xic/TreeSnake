from pathlib import Path
from typing import Annotated

import typer


def     create(
    path: Annotated[
        Path,
        typer.Argument(help="Path to file or directory to create."),
    ],
    directory: Annotated[
        bool,
        typer.Option("--dir", "-d", help="Create a directory instead of a file."),
    ] = False,
) -> None:
    """Create a file or directory at PATH, including any missing parent directories."""
    if directory:
        path.mkdir(parents=True, exist_ok=True)
        typer.echo(f"Directory created: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            typer.echo(f"File already exists: {path}", err=True)
            raise typer.Exit(1)
        path.touch()
        typer.echo(f"File created: {path}")
