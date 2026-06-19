from pathlib import Path
from typing import List, NamedTuple, Optional


class GitignorePatterns(NamedTuple):
    dirs: List[str]
    files: List[str]


class GitignoreParser:
    """Best-effort parser for .gitignore-style ignore files.

    Treesnake's RuleSet only matches a bare item name at a single
    directory level (no path awareness — see core/rule.py), so this
    parser only supports the subset of gitignore syntax that maps onto
    that model without silently changing its meaning:

    - comments ("# ...") and blank lines are skipped
    - a trailing "/" marks a directory-only pattern -> exclude_dirs only
    - a pattern with no trailing "/" matches both files and directories
      (as in real gitignore semantics) -> added to both exclude_dirs and
      exclude_files
    - a leading "/" (root-anchoring) is stripped; treesnake has no notion
      of "anchored to project root" since every directory level is
      checked independently with the same rules

    Lines that can't be represented faithfully by a flat name pattern are
    skipped rather than guessed at, since a wrong guess would silently
    exclude (or fail to exclude) the wrong things:

    - negation ("!pattern") — there is no "un-ignore" in RuleSet
    - any pattern with an internal "/" (e.g. "build/temp") — this
      describes a path relationship, not a single name
    """

    def parse(self, path: str) -> GitignorePatterns:
        try:
            lines = Path(path).read_text(encoding="utf-8").splitlines()
        except OSError:
            return GitignorePatterns(dirs=[], files=[])

        dirs: List[str] = []
        files: List[str] = []

        for raw_line in lines:
            pattern = self._clean(raw_line)
            if pattern is None:
                continue

            if pattern.endswith("/"):
                dirs.append(pattern[:-1])
            else:
                dirs.append(pattern)
                files.append(pattern)

        return GitignorePatterns(dirs=dirs, files=files)

    def _clean(self, raw_line: str) -> Optional[str]:
        line = raw_line.strip()

        if not line or line.startswith("#"):
            return None
        if line.startswith("!"):
            return None
        if line.startswith("/"):
            line = line[1:]
        if not line:
            return None

        bare = line[:-1] if line.endswith("/") else line
        if "/" in bare:
            return None

        return line
