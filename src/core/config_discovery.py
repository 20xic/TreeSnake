from pathlib import Path

from .config_format import CANDIDATE_NAMES

__all__ = ["CANDIDATE_NAMES", "ConfigDiscovery"]


class ConfigDiscovery:
    """Finds the closest treesnake config/ignore file by walking up the
    directory tree from a starting path, stopping at the first match in
    CANDIDATE_NAMES priority order."""

    def find(self, start_path: str) -> str | None:
        current = Path(start_path).resolve()
        if current.is_file():
            current = current.parent

        for directory in (current, *current.parents):
            for name in CANDIDATE_NAMES:
                candidate = directory / name
                if candidate.is_file():
                    return str(candidate)

        return None
