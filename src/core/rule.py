import fnmatch
import re
from abc import ABC, abstractmethod
from typing import NamedTuple

from models import ScanConfig


class IRule(ABC):
    @abstractmethod
    def matches(self, name: str) -> bool:
        raise NotImplementedError


class ExactRule(IRule):
    """Точное совпадение по имени: .git, node_modules"""

    def __init__(self, name: str):
        self.name = name

    def matches(self, name: str) -> bool:
        return self.name == name


class GlobRule(IRule):
    """Шаблон: *.txt, *.exe"""

    def __init__(self, pattern: str):
        self.pattern = pattern

    def matches(self, name: str) -> bool:
        return fnmatch.fnmatch(name, self.pattern)


class RegexRule(IRule):
    """Регулярное выражение: ^test_.*, .*_temp$"""

    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern)

    def matches(self, name: str) -> bool:
        return bool(self.pattern.search(name))


class RuleSet:
    def __init__(self, rules: list[IRule]):
        self.rules = rules

    def matches(self, name: str) -> bool:
        return any(rule.matches(name) for rule in self.rules)

    @staticmethod
    def _is_glob(pattern: str) -> bool:
        return any(c in pattern for c in ("*", "?", "[", "]"))

    @staticmethod
    def _is_regex(pattern: str) -> bool:
        return pattern.startswith("re:") or pattern.startswith("regex:")

    @classmethod
    def from_patterns(cls, patterns: list[str]) -> "RuleSet":
        rules: list[IRule] = []
        for pattern in patterns:
            if cls._is_regex(pattern):
                _, _, expr = pattern.partition(":")
                rules.append(RegexRule(expr.strip()))
            elif cls._is_glob(pattern):
                rules.append(GlobRule(pattern))
            else:
                rules.append(ExactRule(pattern))
        return cls(rules)


class CompiledRules(NamedTuple):
    """ScanConfig, скомпилированный в RuleSet'ы — то, с чем работает сканер."""

    exclude_dirs: RuleSet
    exclude_files: RuleSet
    exclude_content_dirs: RuleSet
    exclude_content_files: RuleSet
    include_dirs: RuleSet
    include_files: RuleSet
    max_depth: int | None
    max_file_size: int | None

    @classmethod
    def from_config(cls, config: ScanConfig) -> "CompiledRules":
        return cls(
            exclude_dirs=RuleSet.from_patterns(config.exclude_dirs),
            exclude_files=RuleSet.from_patterns(config.exclude_files),
            exclude_content_dirs=RuleSet.from_patterns(config.exclude_content_dirs),
            exclude_content_files=RuleSet.from_patterns(config.exclude_content_files),
            include_dirs=RuleSet.from_patterns(config.include_dirs),
            include_files=RuleSet.from_patterns(config.include_files),
            max_depth=config.max_depth,
            max_file_size=config.max_file_size,
        )
