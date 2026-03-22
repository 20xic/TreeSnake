import typer

from .commands.art import art
from .commands.init import init
from .commands.scan import scan
from .commands.version import version_command

app = typer.Typer(
    name="treesnake",
    help="Scan directory trees and export them in various formats.",
    add_completion=False,
)

app.command()(scan)
app.command()(init)
app.command("version")(version_command)
app.command("art")(art)


def main() -> None:
    app()