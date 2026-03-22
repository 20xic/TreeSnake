from pathlib import Path
from typing import Annotated

import typer

from core.creator import FileCreator
from core.template_creator import (
    EnvTemplateCreator,
    JsonTemplateCreator,
    TomlTemplateCreator,
    YamlTemplateCreator,
)

from ..types import ConfigFormat

_CREATORS = {
    ConfigFormat.env: EnvTemplateCreator,
    ConfigFormat.json: JsonTemplateCreator,
    ConfigFormat.yaml: YamlTemplateCreator,
    ConfigFormat.yml: YamlTemplateCreator,
    ConfigFormat.toml: TomlTemplateCreator,
}

_EXT_MAP = {
    ConfigFormat.json: "treesnake.json",
    ConfigFormat.yaml: "treesnake.yaml",
    ConfigFormat.env: ".env.treesnake",
    ConfigFormat.yml: "treesnake.yml",
    ConfigFormat.toml: "treesnake.toml",
}


def init(
    path: Annotated[
        Path,
        typer.Argument(help="Directory where the config file will be created."),
    ] = Path("."),
    fmt: Annotated[
        ConfigFormat,
        typer.Option("--fmt", "-f", help="Config file format."),
    ] = ConfigFormat.json,
) -> None:
    path = path.resolve()
    _CREATORS[fmt](FileCreator()).create(str(path))
    typer.echo(f"Created {path / _EXT_MAP[fmt]}")
