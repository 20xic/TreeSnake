import json

import pytest
import yaml

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
            exclude_contend_dirs=["dist"],
            exclude_content_files=["*.log"],
        ),
        mode="--default",
        output="",
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
