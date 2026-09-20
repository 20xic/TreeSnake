import sys

import typer

from .commands.art import art
from .commands.create import create
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
app.command()(create)
app.command("version")(version_command)
app.command("art")(art)


def _force_utf8_stdio() -> None:
    """Вывод содержит emoji и содержимое файлов в UTF-8. На Windows при
    перенаправлении stdout в файл/pipe Python берёт кодировку консоли
    (cp1252 и т.п.) и падает с UnicodeEncodeError — принудительно UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    _force_utf8_stdio()
    app()
