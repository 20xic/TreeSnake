import sys
from pathlib import Path

# Добавляем корень проекта в путь, чтобы импортировать build.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from build import read_version, write_version_file

write_version_file(read_version())