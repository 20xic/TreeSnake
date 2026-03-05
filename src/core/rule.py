import fnmatch
import re
from abc import ABC, abstractmethod


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
