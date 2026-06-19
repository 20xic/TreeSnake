import json
import os
import tomllib
from abc import ABC, abstractmethod
from typing import List

import yaml
from dotenv import dotenv_values

from models import ScanConfig
from models.scan_template import ScanTemplate

from .gitignore_parser import GitignoreParser


class IConfigReader(ABC):
    @abstractmethod
    def read(self, path: str) -> ScanTemplate:
        raise NotImplementedError


class EnvConfigReader(IConfigReader):
    _LIST_FIELDS = {
        "exclude_dirs",
        "exclude_files",
        "exclude_content_dirs",
        "exclude_content_files",
        "include_dirs",
        "include_files",
    }

    def read(self, path: str) -> ScanTemplate:
        data: dict = {}
        for key, raw_value in dotenv_values(path).items():
            if raw_value is None:
                continue
            field = key.lower()
            if field in self._LIST_FIELDS:
                data[field] = self._parse_list(raw_value)
                continue

            value = raw_value.strip()
            if value:
                # Пустой скаляр ("MAX_DEPTH=") намеренно пропускаем: "" не
                # валидный int, а отсутствие ключа просто включает дефолт
                # самой модели — именно то, что нужно для "значение не задано".
                data[field] = value

        config = ScanConfig.model_validate(data)
        return ScanTemplate(
            config=config,
            mode=data.get("mode", "default") or "default",
            output=data.get("output", "stdout") or "stdout",
            out_file=data.get("out_file") or None,
            use_gitignore=data.get("use_gitignore", True),
        )

    def _parse_list(self, value: str) -> List[str]:
        value = value.strip().strip("[]")
        return [item.strip() for item in value.split(",") if item.strip()]


class YamlConfigReader(IConfigReader):
    def read(self, path: str) -> ScanTemplate:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        config = ScanConfig.model_validate(data.get("config", data))
        return ScanTemplate(
            config=config,
            mode=data.get("mode", "default") or "default",
            output=data.get("output", "stdout") or "stdout",
            out_file=data.get("out_file") or None,
            use_gitignore=data.get("use_gitignore", True),
        )


class TomlConfigReader(IConfigReader):
    def read(self, path: str) -> ScanTemplate:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        config = ScanConfig.model_validate(data.get("config", data))
        return ScanTemplate(
            config=config,
            mode=data.get("mode", "default") or "default",
            output=data.get("output", "stdout") or "stdout",
            out_file=data.get("out_file") or None,
            use_gitignore=data.get("use_gitignore", True),
        )


class JsonConfigReader(IConfigReader):
    def read(self, path: str) -> ScanTemplate:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        config = ScanConfig.model_validate(data.get("config", data))
        return ScanTemplate(
            config=config,
            mode=data.get("mode", "default") or "default",
            output=data.get("output", "stdout") or "stdout",
            out_file=data.get("out_file") or None,
            use_gitignore=data.get("use_gitignore", True),
        )


class TreesnakeIgnoreConfigReader(IConfigReader):
    """.treesnakeignore is gitignore-syntax, not a key/value config file —
    reuses GitignoreParser instead of a structured-format parser. There's
    no mode/output section in this format, so the template falls back to
    the same defaults as an empty config file."""

    def read(self, path: str) -> ScanTemplate:
        patterns = GitignoreParser().parse(path)
        config = ScanConfig(exclude_dirs=patterns.dirs, exclude_files=patterns.files)
        return ScanTemplate(config=config, mode="default", output="stdout")


class ConfigReader(IConfigReader):
    _readers_by_name = {
        ".env": EnvConfigReader,
        ".env.treesnake": EnvConfigReader,
        ".treesnakeignore": TreesnakeIgnoreConfigReader,
    }
    _readers_by_ext = {
        ".yml": YamlConfigReader,
        ".yaml": YamlConfigReader,
        ".toml": TomlConfigReader,
        ".json": JsonConfigReader,
    }

    def read(self, path: str) -> ScanTemplate:
        filename = os.path.basename(path).lower()

        reader_cls = self._readers_by_name.get(filename)
        if reader_cls is None:
            ext = os.path.splitext(filename)[-1]
            reader_cls = self._readers_by_ext.get(ext)

        if reader_cls is None:
            raise ValueError(f"Unsupported config format: {filename!r}")

        return reader_cls().read(path)