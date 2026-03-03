from pydantic import BaseModel


class File(BaseModel):
    name: str
    content: str | None = None
    skip_content: bool = False

    def __repr__(self) -> str:
        if self.skip_content:
            return f"{self.name}  [skipped]"
        if self.content is None:
            return f"{self.name}  [binary or unreadable]"
        return f"{self.name}\n    {self.content}"
