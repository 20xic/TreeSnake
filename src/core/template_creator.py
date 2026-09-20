import os

from models.scan_config import ScanConfig
from models.scan_template import ScanTemplate

from .config_format import ConfigFormat, config_filename
from .creator import IContentCreator
from .template_serializer import (
    EnvTemplateSerializer,
    ITemplateSerializer,
    JsonTemplateSerializer,
    TomlTemplateSerializer,
    YamlTemplateSerializer,
)

DEFAULT_TEMPLATE = ScanTemplate(
    config=ScanConfig(
        exclude_dirs=[".git", "venv", "__pycache__"],
        exclude_files=[
            ".env",
            "*.pyc",
            "re:^\\..*",
            ".gitignore",
            "*.md",
            "LICENSE",
            "*.exe",
            "*.lock",
            "treesnake.exe",
            "treesnake.json",
            "treesnake.toml",
            "treesnake.env",
            "treesnake.yaml",
            "treesnake.yml",
        ],
        exclude_content_dirs=["dist", "build"],
        exclude_content_files=["*.log", "*.lock"],
    ),
    mode="llm",
    output="clipboard",
    use_gitignore=True,
)

SERIALIZERS: dict[ConfigFormat, type[ITemplateSerializer]] = {
    ConfigFormat.env: EnvTemplateSerializer,
    ConfigFormat.json: JsonTemplateSerializer,
    ConfigFormat.yaml: YamlTemplateSerializer,
    ConfigFormat.yml: YamlTemplateSerializer,
    ConfigFormat.toml: TomlTemplateSerializer,
}


class TemplateCreator:
    """Пишет шаблон конфига в `<path>/<имя файла формата>`. Имя файла и
    сериализатор берутся из реестра формата."""

    def __init__(self, file_creator: IContentCreator, fmt: ConfigFormat):
        self._file_creator = file_creator
        self._fmt = fmt

    @property
    def filename(self) -> str:
        return config_filename(self._fmt)

    def create(self, path: str, template: ScanTemplate = DEFAULT_TEMPLATE) -> None:
        content = SERIALIZERS[self._fmt]().serialize(template)
        self._file_creator.create(os.path.join(path, self.filename), content=content)


# Совместимые имена для конкретных форматов.
class EnvTemplateCreator(TemplateCreator):
    def __init__(self, file_creator: IContentCreator):
        super().__init__(file_creator, ConfigFormat.env)


class JsonTemplateCreator(TemplateCreator):
    def __init__(self, file_creator: IContentCreator):
        super().__init__(file_creator, ConfigFormat.json)


class YamlTemplateCreator(TemplateCreator):
    def __init__(self, file_creator: IContentCreator):
        super().__init__(file_creator, ConfigFormat.yml)


class TomlTemplateCreator(TemplateCreator):
    def __init__(self, file_creator: IContentCreator):
        super().__init__(file_creator, ConfigFormat.toml)
