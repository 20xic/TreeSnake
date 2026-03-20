from abc import ABC, abstractmethod

from models.scan_config import ScanConfig
from models.scan_template import ScanTemplate

from .creator import IContentCreator

_default_template = ScanTemplate(
    config=ScanConfig(
        exclude_dirs=[".git", "venv", "__pycache__"],
        exclude_files=[".env", "*.pyc", "re:^\\..*"],  # re: скрытые файлы
        exclude_contend_dirs=["dist", "build"],
        exclude_content_files=["*.log", "*.lock"],
    ),
    mode="--llm",
    output="--buffer",
)

CONFIG_FILE_NAME = "treesnake"


class ITemplateCreator(ABC):
    def __init__(self, file_creator: IContentCreator):
        self._file_creator = file_creator

    @abstractmethod
    def create(self, path: str, template: ScanTemplate) -> None:
        raise NotImplementedError


class EnvTemplateCreator(ITemplateCreator):
    def create(self, path: str, template: ScanTemplate = _default_template) -> None:
        self._file_creator.create(
            f"{path}/.env.{CONFIG_FILE_NAME}", content=template.to_env()
        )


class JsonTemplateCreator(ITemplateCreator):
    def create(self, path: str, template: ScanTemplate = _default_template) -> None:
        self._file_creator.create(
            f"{path}/{CONFIG_FILE_NAME}.json", content=template.to_json()
        )


class YamlTemplateCreator(ITemplateCreator):
    def create(self, path: str, template: ScanTemplate = _default_template) -> None:
        self._file_creator.create(
            f"{path}/{CONFIG_FILE_NAME}.yml", content=template.to_yaml()
        )


class TomlTemplateCreator(ITemplateCreator):
    def create(self, path: str, template: ScanTemplate = _default_template) -> None:
        self._file_creator.create(
            f"{path}/{CONFIG_FILE_NAME}.toml", content=template.to_toml()
        )
