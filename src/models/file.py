from dataclasses import dataclass


@dataclass(slots=True)
class File:
    name: str
    content: str
    size: int
