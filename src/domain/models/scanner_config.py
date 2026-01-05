from dataclasses import dataclass
from typing import List


@dataclass
class ScannerConfig:
    exclude_dirs: List[str]
    exclude_patterns: List[str]
    exclude_content_dirs: List[str]
    exclude_content_patterns: List[str]
    structure_only: bool
    llm_mode: bool