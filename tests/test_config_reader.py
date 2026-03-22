import json

import pytest
import yaml

from core.config_reader import (
    ConfigReader,
    EnvConfigReader,
    JsonConfigReader,
    TomlConfigReader,
    YamlConfigReader,
)


@pytest.fixture
def scan_config_data():
    return {
        "exclude_dirs": [".git", "venv"],
        "exclude_files": ["*.pyc"],
        "exclude_content_dirs": ["dist"],
        "exclude_content_files": ["*.log"],
    }


class TestEnvConfigReader:
    def test_read(self, tmp_path, scan_config_data):
        file = tmp_path / ".env"
        file.write_text(
            "EXCLUDE_DIRS=[.git, venv]\n"
            "EXCLUDE_FILES=[*.pyc]\n"
            "EXCLUDE_CONTENT_DIRS=[dist]\n"
            "EXCLUDE_CONTENT_FILES=[*.log]\n",
            encoding="utf-8",
        )

        result = EnvConfigReader().read(str(file))

        assert result.config.exclude_dirs == scan_config_data["exclude_dirs"]
        assert result.config.exclude_files == scan_config_data["exclude_files"]

    def test_empty(self, tmp_path):
        file = tmp_path / ".env"
        file.write_text("", encoding="utf-8")

        result = EnvConfigReader().read(str(file))

        assert result.config.exclude_dirs == []
        assert result.config.exclude_files == []


class TestJsonConfigReader:
    def test_read(self, tmp_path, scan_config_data):
        file = tmp_path / "config.json"
        file.write_text(json.dumps({"config": scan_config_data}), encoding="utf-8")

        result = JsonConfigReader().read(str(file))

        assert result.config.exclude_dirs == scan_config_data["exclude_dirs"]
        assert result.config.exclude_files == scan_config_data["exclude_files"]

    def test_empty(self, tmp_path):
        file = tmp_path / "config.json"
        file.write_text("{}", encoding="utf-8")

        result = JsonConfigReader().read(str(file))

        assert result.config.exclude_dirs == []


class TestYamlConfigReader:
    def test_read(self, tmp_path, scan_config_data):
        file = tmp_path / "config.yml"
        file.write_text(yaml.dump({"config": scan_config_data}), encoding="utf-8")

        result = YamlConfigReader().read(str(file))

        assert result.config.exclude_dirs == scan_config_data["exclude_dirs"]
        assert result.config.exclude_files == scan_config_data["exclude_files"]

    def test_empty(self, tmp_path):
        file = tmp_path / "config.yml"
        file.write_text("", encoding="utf-8")

        result = YamlConfigReader().read(str(file))

        assert result.config.exclude_dirs == []


class TestTomlConfigReader:
    def test_read(self, tmp_path, scan_config_data):
        file = tmp_path / "config.toml"
        file.write_text(
            "[config]\n"
            'exclude_dirs = [".git", "venv"]\n'
            'exclude_files = ["*.pyc"]\n'
            'exclude_content_dirs = ["dist"]\n'
            'exclude_content_files = ["*.log"]\n',
            encoding="utf-8",
        )

        result = TomlConfigReader().read(str(file))

        assert result.config.exclude_dirs == scan_config_data["exclude_dirs"]
        assert result.config.exclude_files == scan_config_data["exclude_files"]

    def test_empty(self, tmp_path):
        file = tmp_path / "config.toml"
        file.write_text("", encoding="utf-8")

        result = TomlConfigReader().read(str(file))

        assert result.config.exclude_dirs == []


class TestConfigReader:
    @pytest.mark.parametrize(
        "filename, content",
        [
            (".env", "EXCLUDE_DIRS=[.git]\nEXCLUDE_FILES=[*.pyc]\n"),
            (
                "config.json",
                '{"config": {"exclude_dirs": [".git"], "exclude_files": ["*.pyc"]}}',
            ),
            (
                "config.yml",
                "config:\n  exclude_dirs:\n    - .git\n  exclude_files:\n    - '*.pyc'\n",
            ),
            (
                "config.toml",
                '[config]\nexclude_dirs = [".git"]\nexclude_files = ["*.pyc"]\n',
            ),
        ],
    )
    def test_reads_by_extension(self, tmp_path, filename, content):
        file = tmp_path / filename
        file.write_text(content, encoding="utf-8")

        result = ConfigReader().read(str(file))

        assert ".git" in result.config.exclude_dirs

    def test_unsupported_extension(self, tmp_path):
        file = tmp_path / "config.xml"
        file.write_text("<config/>", encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported config format"):
            ConfigReader().read(str(file))
