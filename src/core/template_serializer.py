import json
from abc import ABC, abstractmethod

import yaml

from models.scan_template import ScanTemplate


class ITemplateSerializer(ABC):
    @abstractmethod
    def serialize(self, template: ScanTemplate) -> str:
        raise NotImplementedError


class EnvTemplateSerializer(ITemplateSerializer):
    """`config`'s fields are flattened to the top level (EXCLUDE_DIRS=,
    MAX_DEPTH=, ...) rather than written as one nested CONFIG= blob —
    EnvConfigReader reads flat top-level keys, so the previous nested
    form silently lost every exclude_*/include_*/max_* setting on
    round-trip (it was never actually parsed back)."""

    def serialize(self, template: ScanTemplate) -> str:
        data = template.model_dump()
        config_data = data.pop("config")

        lines = [self._format_field(field, value) for field, value in config_data.items()]
        lines.extend(self._format_field(field, value) for field, value in data.items())
        return "\n".join(lines)

    def _format_field(self, field: str, value) -> str:
        if isinstance(value, list):
            return f"{field.upper()}=[{', '.join(value)}]"
        if value is None:
            return f"{field.upper()}="
        return f"{field.upper()}={value}"


class JsonTemplateSerializer(ITemplateSerializer):
    def serialize(self, template: ScanTemplate) -> str:
        return json.dumps(template.model_dump(), indent=4)


class YamlTemplateSerializer(ITemplateSerializer):
    def serialize(self, template: ScanTemplate) -> str:
        return yaml.dump(
            template.model_dump(), default_flow_style=False, allow_unicode=True
        )


class TomlTemplateSerializer(ITemplateSerializer):
    """Hand-rolled TOML writer — the stdlib only ships `tomllib` for
    reading, not writing. `config` must be emitted as a proper [config]
    subtable (not a single quoted Python-repr string): TOML requires all
    root-level key=value pairs to come before any [table] header, so
    `config` is popped out and written last."""

    def serialize(self, template: ScanTemplate) -> str:
        data = template.model_dump()
        config_data = data.pop("config")

        lines = [
            self._format_field(field, value)
            for field, value in data.items()
            if value is not None
        ]
        lines.append("")
        lines.append("[config]")
        lines.extend(
            self._format_field(field, value)
            for field, value in config_data.items()
            if value is not None
        )
        return "\n".join(lines)

    def _format_field(self, field: str, value) -> str:
        if isinstance(value, bool):
            return f"{field} = {'true' if value else 'false'}"
        if isinstance(value, list):
            items = ", ".join(self._quote(v) for v in value)
            return f"{field} = [{items}]"
        if isinstance(value, (int, float)):
            return f"{field} = {value}"
        return f"{field} = {self._quote(value)}"

    @staticmethod
    def _quote(value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'