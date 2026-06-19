from pathlib import Path
from typing import List, Optional

CANDIDATE_NAMES: List[str] = [
    "treesnake.json",
    "treesnake.toml",
    "treesnake.yaml",
    "treesnake.yml",
    ".env.treesnake",
    ".treesnakeignore",
]


class ConfigDiscovery:
    """Finds the closest treesnake config/ignore file by walking up the
    directory tree from a starting path, stopping at the first match in
    CANDIDATE_NAMES priority order."""

    def find(self, start_path: str) -> Optional[str]:
        current = Path(start_path).resolve()
        if current.is_file():
            current = current.parent

        for directory in (current, *current.parents):
            for name in CANDIDATE_NAMES:
                candidate = directory / name
                if candidate.is_file():
                    return str(candidate)

        return None