from dataclasses import dataclass

@dataclass
class File:
    name:str
    content:str|None

    def __repr__(self) -> str:
        return f"{self.name}\n\t{self.content}"


