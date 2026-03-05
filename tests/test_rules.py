from core.rule import ExactRule, GlobRule, RegexRule, RuleSet


class TestExactRule:
    def test_matches(self):
        assert ExactRule(".git").matches(".git")

    def test_not_matches(self):
        assert not ExactRule(".git").matches(".github")


class TestGlobRule:
    def test_matches(self):
        assert GlobRule("*.txt").matches("file.txt")

    def test_not_matches(self):
        assert not GlobRule("*.txt").matches("file.py")

    def test_matches_wildcard(self):
        assert GlobRule("test_*").matches("test_file.py")


class TestRegexRule:
    def test_matches(self):
        assert RegexRule(r"^\..*").matches(".hidden")

    def test_not_matches(self):
        assert not RegexRule(r"^\..*").matches("visible")


class TestRuleSet:
    def test_exact_pattern(self):
        ruleset = RuleSet.from_patterns([".git"])
        assert ruleset.matches(".git")
        assert not ruleset.matches(".github")

    def test_glob_pattern(self):
        ruleset = RuleSet.from_patterns(["*.pyc"])
        assert ruleset.matches("file.pyc")
        assert not ruleset.matches("file.py")

    def test_regex_pattern(self):
        ruleset = RuleSet.from_patterns(["re:^test_.*"])
        assert ruleset.matches("test_file.py")
        assert not ruleset.matches("file.py")

    def test_multiple_patterns(self):
        ruleset = RuleSet.from_patterns([".git", "*.pyc", "re:^temp_.*"])
        assert ruleset.matches(".git")
        assert ruleset.matches("file.pyc")
        assert ruleset.matches("temp_file.py")
        assert not ruleset.matches("main.py")

    def test_empty_patterns(self):
        assert not RuleSet.from_patterns([]).matches("anything")
