import json
from abc import ABC, abstractmethod

import yaml

from models.scan_template import ScanTemplate


class ITemplateSerializer(ABC):
    @abstractmethod
    def serialize(self, template: ScanTemplate) -> str:
        raise NotImplementedError


class EnvTemplateSerializer(ITemplateSerializer):
    def serialize(self, template: ScanTemplate) -> str:
        lines = []
        for field, value in template.model_dump().items():
            if isinstance(value, list):
                lines.append(f"{field.upper()}=[{', '.join(value)}]")
            elif value is None:
                lines.append(f"{field.upper()}=")
            else:
                lines.append(f"{field.upper()}={value}")
        return "\n".join(lines)


class JsonTemplateSerializer(ITemplateSerializer):
    def serialize(self, template: ScanTemplate) -> str:
        return json.dumps(template.model_dump(), indent=4)


class YamlTemplateSerializer(ITemplateSerializer):
    def serialize(self, template: ScanTemplate) -> str:
        return yaml.dump(
            template.model_dump(), default_flow_style=False, allow_unicode=True
        )


class TomlTemplateSerializer(ITemplateSerializer):
    def serialize(self, template: ScanTemplate) -> str:
        lines = []
        for field, value in template.model_dump().items():
            if isinstance(value, list):
                items = ", ".join(f'"{v}"' for v in value)
                lines.append(f"{field} = [{items}]")
            elif value is None:
                lines.append(f'{field} = ""')
            else:
                lines.append(f'{field} = "{value}"')
        return "\n".join(lines)