from cli.utils import apply_gitignore
from models import ScanConfig


class TestApplyGitignore:
    def test_returns_same_config_when_no_gitignore_present(self, tmp_path):
        config = ScanConfig(exclude_dirs=["venv"])

        result = apply_gitignore(config, tmp_path)

        assert result.exclude_dirs == ["venv"]
        assert result.exclude_files == []

    def test_merges_patterns_additively(self, tmp_path):
        (tmp_path / ".gitignore").write_text("*.pyc\ndist/\n", encoding="utf-8")
        config = ScanConfig(exclude_dirs=["venv"], exclude_files=["*.log"])

        result = apply_gitignore(config, tmp_path)

        assert set(result.exclude_dirs) == {"venv", "dist", "*.pyc"}
        assert set(result.exclude_files) == {"*.log", "*.pyc"}

    def test_does_not_mutate_original_config(self, tmp_path):
        (tmp_path / ".gitignore").write_text("dist/\n", encoding="utf-8")
        config = ScanConfig(exclude_dirs=["venv"])

        apply_gitignore(config, tmp_path)

        assert config.exclude_dirs == ["venv"]

    def test_deduplicates_overlapping_patterns(self, tmp_path):
        (tmp_path / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
        config = ScanConfig(exclude_files=["*.pyc"])

        result = apply_gitignore(config, tmp_path)

        assert result.exclude_files.count("*.pyc") == 1

    def test_empty_gitignore_leaves_config_unchanged(self, tmp_path):
        (tmp_path / ".gitignore").write_text("", encoding="utf-8")
        config = ScanConfig(exclude_dirs=["venv"])

        result = apply_gitignore(config, tmp_path)

        assert result.exclude_dirs == ["venv"]

    def test_preserves_other_config_fields(self, tmp_path):
        (tmp_path / ".gitignore").write_text("dist/\n", encoding="utf-8")
        config = ScanConfig(max_depth=2, max_file_size=1024, include_files=["*.py"])

        result = apply_gitignore(config, tmp_path)

        assert result.max_depth == 2
        assert result.max_file_size == 1024
        assert result.include_files == ["*.py"]