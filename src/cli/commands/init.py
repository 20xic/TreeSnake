from pathlib import Path
from typing import Annotated

import typer

from core.creator import FileCreator
from core.gitignore_manager import GitignoreManager
from core.template_creator import DEFAULT_TEMPLATE, TemplateCreator

from ..types import ConfigFormat


def init(
    path: Annotated[
        Path,
        typer.Argument(help="Directory where the config file will be created."),
    ] = Path("."),
    fmt: Annotated[
        ConfigFormat,
        typer.Option("--fmt", "-f", help="Config file format."),
    ] = ConfigFormat.json,
    use_gitignore: Annotated[
        bool,
        typer.Option(
            "--gitignore/--no-gitignore",
            help=(
                "Value written for the use_gitignore setting in the generated "
                "config (controls whether `scan` additionally excludes patterns "
                "from .gitignore when this config is used). Enabled by default; "
                "the field stays editable in the file afterwards either way."
            ),
        ),
    ] = True,
) -> None:
    path = path.resolve()
    template = DEFAULT_TEMPLATE.model_copy(update={"use_gitignore": use_gitignore})
    creator = TemplateCreator(FileCreator(), fmt)
    creator.create(str(path), template=template)
    typer.echo(f"Created {path / creator.filename}")

    GitignoreManager(path / ".gitignore").update()
    typer.echo(f"Updated {path / '.gitignore'}")
