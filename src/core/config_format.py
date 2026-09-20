"""Единый реестр форматов конфига.

Всё, что зависит от формата — имя файла для `init`, список кандидатов для
автопоиска, выбор reader'а и serializer'а — выводится отсюда, чтобы при
добавлении формата не приходилось синхронизировать несколько словарей
в разных модулях.
"""

from enum import Enum

CONFIG_BASENAME = "treesnake"

# gitignore-подобный файл: не формат ScanTemplate, но участвует в автопоиске
IGNORE_FILENAME = ".treesnakeignore"


class ConfigFormat(str, Enum):
    env = "env"
    json = "json"
    yaml = "yaml"
    toml = "toml"
    yml = "yml"


CONFIG_FILENAMES: dict[ConfigFormat, str] = {
    ConfigFormat.json: f"{CONFIG_BASENAME}.json",
    ConfigFormat.toml: f"{CONFIG_BASENAME}.toml",
    ConfigFormat.yaml: f"{CONFIG_BASENAME}.yaml",
    ConfigFormat.yml: f"{CONFIG_BASENAME}.yml",
    ConfigFormat.env: f".env.{CONFIG_BASENAME}",
}

# Порядок = приоритет при автопоиске (ConfigDiscovery).
CANDIDATE_NAMES: list[str] = [*CONFIG_FILENAMES.values(), IGNORE_FILENAME]


def config_filename(fmt: ConfigFormat) -> str:
    return CONFIG_FILENAMES[fmt]
