from typing import List, NamedTuple, Optional
from pydantic import BaseModel, ConfigDict

from core.rule import RuleSet


class CompiledRules(NamedTuple):
    exclude_dirs: "RuleSet"
    exclude_files: "RuleSet"
    exclude_content_dirs: "RuleSet"
    exclude_content_files: "RuleSet"
    include_dirs: "RuleSet"
    include_files: "RuleSet"
    max_depth: Optional[int]
    max_file_size: Optional[int]


class ScanConfig(BaseModel):
    exclude_dirs: List[str] = []
    exclude_files: List[str] = []
    exclude_content_dirs: List[str] = []
    exclude_content_files: List[str] = []
    include_dirs: List[str] = []
    include_files: List[str] = []
    max_depth: Optional[int] = None
    max_file_size: Optional[int] = None

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