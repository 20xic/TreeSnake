import os
from abc import ABC, abstractmethod


class ICreator(ABC):
    @abstractmethod
    def create(self, path: str) -> None:
        raise NotImplementedError


class IContentCreator(ICreator, ABC):
    @abstractmethod
    def create(self, path: str, content: str = "") -> None:
        raise NotImplementedError


class FileCreator(IContentCreator):
    def create(self, path: str, content: str = "") -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


class DirectoryCreator(ICreator):
    def create(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
