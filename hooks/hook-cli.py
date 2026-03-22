import tomllib
from pathlib import Path

pyproject = Path("pyproject.toml")
with open(pyproject, "rb") as f:
    version = tomllib.load(f)["project"]["version"]

version_file = Path("src/cli/_version.py")
version_file.write_text(f'__version__ = "{version}"\n')
