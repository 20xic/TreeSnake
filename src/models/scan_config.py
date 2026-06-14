from typing import List, NamedTuple
from pydantic import BaseModel, ConfigDict

from core.rule import RuleSet

class CompiledRules(NamedTuple):
    exclude_dirs: "RuleSet"
    exclude_files: "RuleSet"
    exclude_content_dirs: "RuleSet"
    exclude_content_files: "RuleSet"


class ScanConfig(BaseModel):
    exclude_dirs: List[str] = []
    exclude_files: List[str] = []
    exclude_content_dirs: List[str] = []
    exclude_content_files: List[str] = []

    model_config = ConfigDict(from_attributes=True)

    def compile(self) -> "CompiledRules":
      
        return CompiledRules(
            exclude_dirs=RuleSet.from_patterns(self.exclude_dirs),
            exclude_files=RuleSet.from_patterns(self.exclude_files),
            exclude_content_dirs=RuleSet.from_patterns(self.exclude_content_dirs),
            exclude_content_files=RuleSet.from_patterns(self.exclude_content_files),
        )