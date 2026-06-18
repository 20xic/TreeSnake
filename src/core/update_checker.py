import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

GITHUB_RELEASES_URL = "https://api.github.com/repos/20xic/treesnake/releases/latest"
DEFAULT_CACHE_PATH = Path.home() / ".treesnake" / "update_check.json"
CACHE_TTL_SECONDS = 24 * 60 * 60
REQUEST_TIMEOUT_SECONDS = 2


def _parse_version(version: str) -> Tuple[int, ...]:
    """Parses a dotted version string into a tuple of ints for comparison.

    Best-effort: non-numeric prefixes within a segment (e.g. "1.0.0-rc1")
    are truncated at the first non-digit character. Missing/garbage
    segments become 0 rather than raising, since version strings come
    from an external API (GitHub tag names) and may not be well-formed.
    """
    parts = []
    for segment in version.strip().lstrip("v").split("."):
        digits = ""
        for char in segment:
            if char.isdigit():
                digits += char
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _is_newer(candidate: str, baseline: str) -> bool:
    """True if `candidate` version is strictly greater than `baseline`."""
    a = _parse_version(candidate)
    b = _parse_version(baseline)
    length = max(len(a), len(b))
    a = a + (0,) * (length - len(a))
    b = b + (0,) * (length - len(b))
    return a > b


class UpdateChecker:
    """Checks GitHub Releases for a newer treesnake version.

    Designed to run in a background ``threading.Thread`` started by the
    caller — ``check()`` never raises, so network failures fail silently
    and never break a scan. The thread should NOT be a daemon thread:
    on a cache miss this method makes a real network call, which is
    almost always slower than the scan itself, so a daemon thread would
    get killed mid-write before the cache file is ever persisted. A
    plain (non-daemon) thread lets the interpreter wait for it to finish
    at process exit (bounded by ``REQUEST_TIMEOUT_SECONDS``) without
    delaying the scan's own visible output. Results are cached on disk
    for ``CACHE_TTL_SECONDS`` so this network call only happens once a
    day at most.
    """

    def __init__(self, current_version: str, cache_path: Path = DEFAULT_CACHE_PATH):
        self._current_version = current_version
        self._cache_path = cache_path
        self.latest_version: Optional[str] = None
        self.release_url: Optional[str] = None

    def check(self) -> None:
        try:
            cached = self._read_cache()
            if cached is not None:
                self.latest_version = cached.get("latest_version")
                self.release_url = cached.get("release_url")
                return

            latest_version, release_url = self._fetch()
            if latest_version is None:
                return

            self.latest_version = latest_version
            self.release_url = release_url
            self._write_cache(latest_version, release_url)
        except Exception:
            # Любая ошибка (сеть, диск, парсинг) — тихий фейл.
            # Проверка обновлений никогда не должна ломать сканирование.
            pass

    def has_update(self) -> bool:
        if not self.latest_version:
            return False
        return _is_newer(self.latest_version, self._current_version)

    def _read_cache(self) -> Optional[dict]:
        if not self._cache_path.exists():
            return None
        try:
            data = json.loads(self._cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - data.get("checked_at", 0) > CACHE_TTL_SECONDS:
            return None
        return data

    def _write_cache(self, latest_version: str, release_url: Optional[str]) -> None:
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_path.write_text(
            json.dumps(
                {
                    "checked_at": time.time(),
                    "latest_version": latest_version,
                    "release_url": release_url,
                }
            ),
            encoding="utf-8",
        )

    def _fetch(self) -> Tuple[Optional[str], Optional[str]]:
        request = urllib.request.Request(
            GITHUB_RELEASES_URL,
            headers={"Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))

        tag = data.get("tag_name") or ""
        version = tag.lstrip("v") if tag else None
        return version, data.get("html_url")