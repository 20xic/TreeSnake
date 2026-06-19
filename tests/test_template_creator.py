import json

import pytest
import yaml

from core.config_reader import ConfigReader
from core.creator import FileCreator
from core.template_creator import (
    EnvTemplateCreator,
    JsonTemplateCreator,
    TomlTemplateCreator,
    YamlTemplateCreator,
)
from models import ScanConfig, ScanTemplate


@pytest.fixture
def template():
    return ScanTemplate(
        config=ScanConfig(
            exclude_dirs=[".git", "venv"],
            exclude_files=["*.pyc"],
            exclude_content_dirs=["dist"],
            exclude_content_files=["*.log"],
        ),
        mode="default",
        output="stdout",
    )


@pytest.fixture
def creators(tmp_path):
    file_creator = FileCreator()
    return {
        "env": (EnvTemplateCreator(file_creator), tmp_path / ".env.treesnake"),
        "json": (JsonTemplateCreator(file_creator), tmp_path / "treesnake.json"),
        "yaml": (YamlTemplateCreator(file_creator), tmp_path / "treesnake.yml"),
        "toml": (TomlTemplateCreator(file_creator), tmp_path / "treesnake.toml"),
    }


class TestTemplateCreators:
    def test_env_creates_file(self, tmp_path, creators, template):
        creator, path = creators["env"]
        creator.create(str(tmp_path), template)
        assert path.exists()

    def test_env_contains_values(self, tmp_path, creators, template):
        creator, path = creators["env"]
        creator.create(str(tmp_path), template)
        content = path.read_text()
        assert ".git" in content
        assert "*.pyc" in content

    def test_json_valid(self, tmp_path, creators, template):
        creator, path = creators["json"]
        creator.create(str(tmp_path), template)
        data = json.loads(path.read_text())
        assert "config" in data
        assert ".git" in data["config"]["exclude_dirs"]

    def test_yaml_valid(self, tmp_path, creators, template):
        creator, path = creators["yaml"]
        creator.create(str(tmp_path), template)
        data = yaml.safe_load(path.read_text())
        assert ".git" in data["config"]["exclude_dirs"]

    def test_toml_creates_file(self, tmp_path, creators, template):
        creator, path = creators["toml"]
        creator.create(str(tmp_path), template)
        assert path.exists()
        assert ".git" in path.read_text()


@pytest.fixture
def creator_and_extension(tmp_path):
    file_creator = FileCreator()
    return {
        "env": (EnvTemplateCreator(file_creator), ".env.treesnake"),
        "json": (JsonTemplateCreator(file_creator), "treesnake.json"),
        "yaml": (YamlTemplateCreator(file_creator), "treesnake.yml"),
        "toml": (TomlTemplateCreator(file_creator), "treesnake.toml"),
    }


class TestTemplateRoundTrip:
    """Writes a template with each serializer, then reads it straight back
    via ConfigReader (the real consumer, not a format-specific reader) —
    this is the path that was actually broken for TOML and ENV before
    this fix: both happily wrote a file, but neither could be parsed back
    into the original settings."""

    @pytest.mark.parametrize("fmt", ["env", "json", "yaml", "toml"])
    def test_exclude_lists_survive_round_trip(self, tmp_path, creator_and_extension, fmt):
        creator, filename = creator_and_extension[fmt]
        template = ScanTemplate(
            config=ScanConfig(
                exclude_dirs=[".git", "venv"],
                exclude_files=["*.pyc"],
                exclude_content_dirs=["dist"],
                exclude_content_files=["*.log"],
            ),
            mode="llm",
            output="clipboard",
        )
        creator.create(str(tmp_path), template)

        result = ConfigReader().read(str(tmp_path / filename))

        assert result.config.exclude_dirs == [".git", "venv"]
        assert result.config.exclude_files == ["*.pyc"]
        assert result.config.exclude_content_dirs == ["dist"]
        assert result.config.exclude_content_files == ["*.log"]
        assert result.mode == "llm"
        assert result.output == "clipboard"

    @pytest.mark.parametrize("fmt", ["env", "json", "yaml", "toml"])
    @pytest.mark.parametrize("flag_value", [True, False])
    def test_use_gitignore_survives_round_trip(
        self, tmp_path, creator_and_extension, fmt, flag_value
    ):
        creator, filename = creator_and_extension[fmt]
        template = ScanTemplate(config=ScanConfig(), use_gitignore=flag_value)
        creator.create(str(tmp_path), template)

        result = ConfigReader().read(str(tmp_path / filename))

        assert result.use_gitignore is flag_value

    @pytest.mark.parametrize(
        "filename, content",
        [
            (".env.treesnake", "EXCLUDE_DIRS=[.git]\n"),
            ("treesnake.json", '{"config": {"exclude_dirs": [".git"]}}'),
            ("treesnake.yml", "config:\n  exclude_dirs:\n    - .git\n"),
            ("treesnake.toml", '[config]\nexclude_dirs = [".git"]\n'),
        ],
    )
    def test_use_gitignore_defaults_true_when_absent_from_file(
        self, tmp_path, filename, content
    ):
        path = tmp_path / filename
        path.write_text(content, encoding="utf-8")

        result = ConfigReader().read(str(path))

        assert result.use_gitignore is True

    @pytest.mark.parametrize("fmt", ["env", "toml"])
    def test_regex_pattern_with_backslash_survives_round_trip(
        self, tmp_path, creator_and_extension, fmt
    ):
        creator, filename = creator_and_extension[fmt]
        template = ScanTemplate(config=ScanConfig(exclude_files=["re:^\\..*", "*.pyc"]))
        creator.create(str(tmp_path), template)

        result = ConfigReader().read(str(tmp_path / filename))

        assert "re:^\\..*" in result.config.exclude_files
        assert "*.pyc" in result.config.exclude_files

    @pytest.mark.parametrize("fmt", ["env", "json", "yaml", "toml"])
    def test_unset_max_depth_and_max_file_size_survive_round_trip(
        self, tmp_path, creator_and_extension, fmt
    ):
        creator, filename = creator_and_extension[fmt]
        template = ScanTemplate(config=ScanConfig())  # max_depth/max_file_size unset
        creator.create(str(tmp_path), template)

        result = ConfigReader().read(str(tmp_path / filename))

        assert result.config.max_depth is None
        assert result.config.max_file_size is None

    @pytest.mark.parametrize("fmt", ["env", "json", "yaml", "toml"])
    def test_set_max_depth_and_max_file_size_survive_round_trip(
        self, tmp_path, creator_and_extension, fmt
    ):
        creator, filename = creator_and_extension[fmt]
        template = ScanTemplate(config=ScanConfig(max_depth=3, max_file_size=2048))
        creator.create(str(tmp_path), template)

        result = ConfigReader().read(str(tmp_path / filename))

        assert result.config.max_depth == 3
        assert result.config.max_file_size == 2048