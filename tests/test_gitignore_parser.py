from core.gitignore_parser import GitignoreParser


class TestGitignoreParser:
    def test_plain_pattern_matches_both_dirs_and_files(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n", encoding="utf-8")

        result = GitignoreParser().parse(str(gitignore))

        assert "*.pyc" in result.dirs
        assert "*.pyc" in result.files

    def test_trailing_slash_is_dirs_only(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("dist/\n", encoding="utf-8")

        result = GitignoreParser().parse(str(gitignore))

        assert result.dirs == ["dist"]
        assert result.files == []

    def test_blank_lines_are_skipped(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\n\n\n__pycache__\n", encoding="utf-8")

        result = GitignoreParser().parse(str(gitignore))

        assert set(result.files) == {"*.log", "__pycache__"}

    def test_comments_are_skipped(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("# build artifacts\ndist/\n# logs\n*.log\n", encoding="utf-8")

        result = GitignoreParser().parse(str(gitignore))

        assert result.dirs == ["dist", "*.log"]
        assert "*.log" in result.files

    def test_leading_slash_is_stripped(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("/build\n", encoding="utf-8")

        result = GitignoreParser().parse(str(gitignore))

        assert "build" in result.dirs
        assert "build" in result.files

    def test_negation_is_skipped(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.log\n!important.log\n", encoding="utf-8")

        result = GitignoreParser().parse(str(gitignore))

        assert "*.log" in result.files
        assert "!important.log" not in result.files
        assert "important.log" not in result.files

    def test_nested_path_pattern_is_skipped(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("build/temp\n*.pyc\n", encoding="utf-8")

        result = GitignoreParser().parse(str(gitignore))

        assert "build/temp" not in result.files
        assert "build" not in result.dirs
        assert "*.pyc" in result.files

    def test_anchored_directory_pattern_still_works(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("/node_modules/\n", encoding="utf-8")

        result = GitignoreParser().parse(str(gitignore))

        assert result.dirs == ["node_modules"]

    def test_whitespace_around_pattern_is_trimmed(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("  *.tmp  \n", encoding="utf-8")

        result = GitignoreParser().parse(str(gitignore))

        assert "*.tmp" in result.files

    def test_missing_file_returns_empty_patterns(self, tmp_path):
        missing = tmp_path / "does-not-exist"

        result = GitignoreParser().parse(str(missing))

        assert result.dirs == []
        assert result.files == []

    def test_empty_file_returns_empty_patterns(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("", encoding="utf-8")

        result = GitignoreParser().parse(str(gitignore))

        assert result.dirs == []
        assert result.files == []