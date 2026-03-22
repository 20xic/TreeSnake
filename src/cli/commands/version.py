import typer

def version_command() -> None:
    """Show treesnake version."""
    from cli._version import __version__
    typer.echo(f"treesnake {__version__}")