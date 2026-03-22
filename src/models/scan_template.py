import json
from typing import Literal

import yaml
from pydantic import BaseModel

from .scan_config import ScanConfig


class ScanTemplate(BaseModel):
    config: ScanConfig
    mode: Literal["--json", "--llm", "--default", ""] = ""
    output: Literal["", "--clipboard", "--file"] = ""
    out_file: str | None = None

    def to_env(self) -> str:
        lines = []
        for field, value in self.model_dump().items():
            if isinstance(value, list):
                lines.append(f"{field.upper()}=[{', '.join(value)}]")
            elif value is None:
                lines.append(f"{field.upper()}=")
            else:
                lines.append(f"{field.upper()}={value}")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(self.model_dump(), indent=4)

    def to_yaml(self) -> str:
        return yaml.dump(
            self.model_dump(), default_flow_style=False, allow_unicode=True
        )

    def to_toml(self) -> str:
        lines = []
        for field, value in self.model_dump().items():
            if isinstance(value, list):
                lines.append(
                    f"{field} = [{', '.join(f'{chr(34)}{v}{chr(34)}' for v in value)}]"
                )
            elif value is None:
                lines.append(f'{field} = ""')
            else:
                lines.append(f'{field} = "{value}"')
        return "\n".join(lines)
