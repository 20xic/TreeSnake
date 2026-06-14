from dataclasses import dataclass, field
from time import perf_counter

from models import Directory


@dataclass
class ScanResult:
    directory: Directory
    elapsed: float
    file_count: int
    dir_count: int


@dataclass
class ScanTimer:
    _start: float = field(default_factory=perf_counter, init=False)

    def stop(self) -> float:
        return perf_counter() - self._start