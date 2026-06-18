from pathlib import Path

TREESNAKE_GITIGNORE_ENTRIES = [
    "treesnake",
    "treesnake.exe",
    "treesnake.json",
    "treesnake.toml",
    "treesnake.env",
    "treesnake.yaml",
    "treesnake.yml",
    ".env.treesnake",
    ".treesnake/",
]

_SECTION_HEADER = "# treesnake"


class GitignoreManager:
    def __init__(self, gitignore_path: Path):
        self._path = gitignore_path

    def update(self) -> None:
        existing_lines = self._read()
        missing = self._find_missing(existing_lines)

        if not missing:
            return

        self._append(existing_lines, missing)

    def _read(self) -> list[str]:
        if not self._path.exists():
            return []
        return self._path.read_text(encoding="utf-8").splitlines()

    def _find_missing(self, lines: list[str]) -> list[str]:
        existing = {line.strip() for line in lines}
        return [entry for entry in TREESNAKE_GITIGNORE_ENTRIES if entry not in existing]

    def _append(self, existing_lines: list[str], missing: list[str]) -> None:
        needs_newline = bool(existing_lines) and existing_lines[-1].strip() != ""
        block = (["\n"] if needs_newline else []) + [_SECTION_HEADER] + missing

        self._path.write_text(
            "\n".join(existing_lines + block) + "\n",
            encoding="utf-8",
        )