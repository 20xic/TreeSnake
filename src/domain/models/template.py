from dataclasses import dataclass, field
from typing import List

from src.domain.models.scanner_config import ScannerConfig


@dataclass
class Template(ScannerConfig):
    name: str
    extra_files: List[str] = field(default_factory=list)
    
    def convert_to_scanner_config(self) -> ScannerConfig:
        return ScannerConfig(
            exclude_dirs=self.exclude_dirs.copy() if self.exclude_dirs else [],
            exclude_patterns=self.exclude_patterns.copy() if self.exclude_patterns else [],
            exclude_content_dirs=self.exclude_content_dirs.copy() if self.exclude_content_dirs else [],
            exclude_content_patterns=self.exclude_content_patterns.copy() if self.exclude_content_patterns else [],
            structure_only=self.structure_only,
            llm_mode=self.llm_mode
        )