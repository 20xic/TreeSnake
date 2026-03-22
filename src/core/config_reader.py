import json
import os
import tomllib
from abc import ABC, abstractmethod
from typing import List

import yaml
from dotenv import dotenv_values

from models import ScanConfig
from models.scan_template import ScanTemplate


class IConfigReader(ABC):
    @abstractmethod
    def read(self, path: str) -> ScanTemplate:
        raise NotImplementedError


class EnvConfigReader(IConfigReader):
    def read(self, path: str) -> ScanTemplate:
        data = {k.lower(): self._parse_list(v) for k, v in dotenv_values(path).items()}
        config = ScanConfig.model_validate(data)
        return ScanTemplate(
            config=config,
            mode=data.get("mode", ""),
            output=data.get("output", ""),
            out_file=data.get("out_file") or None,
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
            mode=data.get("mode", ""),
            output=data.get("output", ""),
            out_file=data.get("out_file") or None,
        )


class TomlConfigReader(IConfigReader):
    def read(self, path: str) -> ScanTemplate:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        config = ScanConfig.model_validate(data.get("config", data))
        return ScanTemplate(
            config=config,
            mode=data.get("mode", ""),
            output=data.get("output", ""),
            out_file=data.get("out_file") or None,
        )


class JsonConfigReader(IConfigReader):
    def read(self, path: str) -> ScanTemplate:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        config = ScanConfig.model_validate(data.get("config", data))
        return ScanTemplate(
            config=config,
            mode=data.get("mode", ""),
            output=data.get("output", ""),
            out_file=data.get("out_file") or None,
        )


class ConfigReader(IConfigReader):
    _readers = {
        ".env": EnvConfigReader,
        ".yml": YamlConfigReader,
        ".yaml": YamlConfigReader,
        ".toml": TomlConfigReader,
        ".json": JsonConfigReader,
    }

    def read(self, path: str) -> ScanTemplate:
        filename = os.path.basename(path)
        ext = os.path.splitext(filename)[-1].lower() or f".{filename.lstrip('.')}"
        reader = self._readers.get(ext)

        if reader is None:
            raise ValueError(f"Unsupported config format: {ext!r}")

        return reader().read(path)
