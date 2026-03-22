import typer

from .commands.init import init
from .commands.scan import scan

app = typer.Typer(
    name="treesnake",
    help="Scan directory trees and export them in various formats.",
    add_completion=False,
)

app.command()(scan)
app.command()(init)


def main() -> None:
    app()