from abc import ABC, abstractmethod

from models.scan_config import ScanConfig
from models.scan_template import ScanTemplate

from .creator import IContentCreator
from .template_serializer import (
    EnvTemplateSerializer,
    JsonTemplateSerializer,
    TomlTemplateSerializer,
    YamlTemplateSerializer,
)

DEFAULT_TEMPLATE = ScanTemplate(
    config=ScanConfig(
        exclude_dirs=[".git", "venv", "__pycache__"],
        exclude_files=[
            ".env", "*.pyc", "re:^\\..*", ".gitignore",
            "*.md", "LICENSE", "*.exe", "*.lock",
            "treesnake.exe", "treesnake.json", "treesnake.toml",
            "treesnake.env", "treesnake.yaml", "treesnake.yml",
        ],
        exclude_content_dirs=["dist", "build"],
        exclude_content_files=["*.log", "*.lock"],
    ),
    mode="llm",
    output="clipboard",
    use_gitignore=True,
)

CONFIG_FILE_NAME = "treesnake"


class ITemplateCreator(ABC):
    def __init__(self, file_creator: IContentCreator):
        self._file_creator = file_creator

    @abstractmethod
    def create(self, path: str, template: ScanTemplate = DEFAULT_TEMPLATE) -> None:
        raise NotImplementedError


class EnvTemplateCreator(ITemplateCreator):
    def create(self, path: str, template: ScanTemplate = DEFAULT_TEMPLATE) -> None:
        content = EnvTemplateSerializer().serialize(template)
        self._file_creator.create(f"{path}/.env.{CONFIG_FILE_NAME}", content=content)


class JsonTemplateCreator(ITemplateCreator):
    def create(self, path: str, template: ScanTemplate = DEFAULT_TEMPLATE) -> None:
        content = JsonTemplateSerializer().serialize(template)
        self._file_creator.create(f"{path}/{CONFIG_FILE_NAME}.json", content=content)


class YamlTemplateCreator(ITemplateCreator):
    def create(self, path: str, template: ScanTemplate = DEFAULT_TEMPLATE) -> None:
        content = YamlTemplateSerializer().serialize(template)
        self._file_creator.create(f"{path}/{CONFIG_FILE_NAME}.yml", content=content)


class TomlTemplateCreator(ITemplateCreator):
    def create(self, path: str, template: ScanTemplate = DEFAULT_TEMPLATE) -> None:
        content = TomlTemplateSerializer().serialize(template)
        self._file_creator.create(f"{path}/{CONFIG_FILE_NAME}.toml", content=content)