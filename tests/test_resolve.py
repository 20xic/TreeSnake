from pathlib import Path

import pytest

from cli.resolve import CliFilters, resolve_options
from cli.types import OutputDest, OutputFormat
from models import ScanConfig, ScanTemplate


@pytest.fixture
def template():
    return ScanTemplate(
        config=ScanConfig(exclude_dirs=["node_modules"], exclude_files=["*.log"]),
        mode="llm",
        output="file",
        out_file="out.txt",
        use_gitignore=False,
    )


class TestResolveOptions:
    def test_defaults_without_template(self, tmp_path):
        options = resolve_options(None, CliFilters(), project_root=tmp_path)

        assert options.scan_config == ScanConfig()
        assert options.fmt == OutputFormat.default
        assert options.output == OutputDest.stdout
        assert options.out_file is None

    def test_template_fills_everything(self, tmp_path, template):
        options = resolve_options(template, CliFilters(), project_root=tmp_path)

        assert options.scan_config == template.config
        assert options.fmt == OutputFormat.llm
        assert options.output == OutputDest.file
        assert options.out_file == Path("out.txt")

    def test_any_cli_filter_discards_template_filter_block(self, tmp_path, template):
        options = resolve_options(
            template, CliFilters(max_depth=2), project_root=tmp_path
        )

        assert options.scan_config.exclude_dirs == []
        assert options.scan_config.max_depth == 2
        # но не-фильтровые поля из шаблона остаются
        assert options.fmt == OutputFormat.llm

    def test_cli_lists_are_split_on_whitespace(self, tmp_path):
        options = resolve_options(
            None, CliFilters(exclude_dirs=[".git venv"]), project_root=tmp_path
        )

        assert options.scan_config.exclude_dirs == [".git", "venv"]

    def test_only_tree_keeps_template_filters(self, tmp_path, template):
        options = resolve_options(
            template, CliFilters(), only_tree=True, project_root=tmp_path
        )

        assert options.scan_config.exclude_dirs == ["node_modules"]
        assert options.scan_config.exclude_content_files == ["*"]

    def test_only_tree_does_not_mutate_template(self, tmp_path, template):
        resolve_options(template, CliFilters(), only_tree=True, project_root=tmp_path)

        assert template.config.exclude_content_files == []

    def test_individual_overrides(self, tmp_path, template):
        options = resolve_options(
            template,
            CliFilters(),
            fmt=OutputFormat.xml,
            output=OutputDest.stdout,
            project_root=tmp_path,
        )

        assert options.fmt == OutputFormat.xml
        assert options.output == OutputDest.stdout
        assert options.out_file == Path("out.txt")

    def test_gitignore_default_from_template(self, tmp_path, template):
        (tmp_path / ".gitignore").write_text("build/\n", encoding="utf-8")

        options = resolve_options(template, CliFilters(), project_root=tmp_path)

        assert "build" not in options.scan_config.exclude_dirs

    def test_gitignore_flag_overrides_template(self, tmp_path, template):
        (tmp_path / ".gitignore").write_text("build/\n", encoding="utf-8")

        options = resolve_options(
            template, CliFilters(), use_gitignore=True, project_root=tmp_path
        )

        assert "build" in options.scan_config.exclude_dirs

    def test_gitignore_enabled_by_default_without_template(self, tmp_path):
        (tmp_path / ".gitignore").write_text("build/\n", encoding="utf-8")

        options = resolve_options(None, CliFilters(), project_root=tmp_path)

        assert "build" in options.scan_config.exclude_dirs
