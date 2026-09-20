from typing import NamedTuple

from pydantic import BaseModel, ConfigDict

from core.rule import RuleSet


class CompiledRules(NamedTuple):
    exclude_dirs: "RuleSet"
    exclude_files: "RuleSet"
    exclude_content_dirs: "RuleSet"
    exclude_content_files: "RuleSet"
    include_dirs: "RuleSet"
    include_files: "RuleSet"
    max_depth: int | None
    max_file_size: int | None


class ScanConfig(BaseModel):
    exclude_dirs: list[str] = []
    exclude_files: list[str] = []
    exclude_content_dirs: list[str] = []
    exclude_content_files: list[str] = []
    include_dirs: list[str] = []
    include_files: list[str] = []
    max_depth: int | None = None
    max_file_size: int | None = None

    model_config = ConfigDict(from_attributes=True)

    def compile(self) -> "CompiledRules":

        return CompiledRules(
            exclude_dirs=RuleSet.from_patterns(self.exclude_dirs),
            exclude_files=RuleSet.from_patterns(self.exclude_files),
            exclude_content_dirs=RuleSet.from_patterns(self.exclude_content_dirs),
            exclude_content_files=RuleSet.from_patterns(self.exclude_content_files),
            include_dirs=RuleSet.from_patterns(self.include_dirs),
            include_files=RuleSet.from_patterns(self.include_files),
            max_depth=self.max_depth,
            max_file_size=self.max_file_size,
        )
