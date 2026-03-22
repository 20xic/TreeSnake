from enum import Enum


class OutputFormat(str, Enum):
    default = "default"
    llm = "llm"
    json = "json"


class OutputDest(str, Enum):
    stdout = "stdout"
    file = "file"
    clipboard = "clipboard"


class ConfigFormat(str, Enum):
    env = "env"
    json = "json"
    yaml = "yaml"
    toml = "toml"
    yml = "yml"