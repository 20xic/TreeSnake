from typing import List, Optional
import os
import fnmatch

from src.domain import Directory, File, ScannerConfig
from src.core.logger import logger


class Scanner:
    def __init__(self) -> None:
        pass
    
    def scan(self, root_directory: str, config: ScannerConfig) -> Directory:
        root = os.path.normpath(root_directory)
        
        def scan_recursive(current_path: str, depth: int = 0) -> Optional[Directory]:
            current_dir_name = os.path.basename(current_path)
            
            if self._should_skip(current_path, config.exclude_dirs, config.exclude_patterns):
                return None
            
            skip_content = self._should_skip_dir_content(current_path, config.exclude_content_dirs)
            
            if skip_content:
                return Directory(
                    name=current_dir_name,
                    subdirectories=[],
                    files=[],
                    skip_content=True
                )
            
            subdirectories = []
            files = []
            
            try:
                items = os.listdir(current_path)
            except PermissionError as e:
                logger.warning(f"Permission denied for {current_path}: {e}")
                return Directory(
                    name=current_dir_name,
                    subdirectories=[],
                    files=[File(name="[Permission denied]", content=None)],
                    skip_content=False
                )
            
            dirs = []
            file_items = []
            
            for item in items:
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                elif os.path.isfile(item_path):
                    file_items.append(item)
            
            dirs[:] = [d for d in dirs 
                      if not self._should_skip(os.path.join(current_path, d), 
                                              config.exclude_dirs, 
                                              config.exclude_patterns)]
         
            for dir_name in dirs:
                dir_path = os.path.join(current_path, dir_name)
                subdir = scan_recursive(dir_path, depth + 1)
                if subdir:
                    subdirectories.append(subdir)
            
            for file_name in file_items:
                file_path = os.path.join(current_path, file_name)
                
                if self._should_skip(file_path, config.exclude_dirs, config.exclude_patterns):
                    continue
                
                should_read_content = (
                    not config.structure_only and 
                    not self._should_skip_file_content(file_path, config.exclude_content_patterns)
                )
                
                content = self._read_file_content(file_path) if should_read_content else None
                
                file = File(name=file_name, content=content)
                files.append(file)
            
            return Directory(
                name=current_dir_name,
                subdirectories=subdirectories,
                files=files,
                skip_content=False
            )
        
        result = scan_recursive(root)
        if result is None:
            return Directory(
                name=os.path.basename(root),
                subdirectories=[],
                files=[File(name="[Directory excluded by filters]", content=None)],
                skip_content=False
            )
        
        return result
    
    def _should_skip(self, path: str, exclude_dirs: List[str], exclude_patterns: List[str]) -> bool:
        for excl_dir in exclude_dirs:
            if excl_dir in path.split(os.sep):
                return True
        
        if os.path.isfile(path):
            filename = os.path.basename(path)
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    return True
        
        return False
    
    def _should_skip_dir_content(self, dir_path: str, exclude_content_dirs: List[str]) -> bool:
        for excl_dir in exclude_content_dirs:
            if excl_dir in dir_path.split(os.sep):
                return True
        return False
    
    def _should_skip_file_content(self, file_path: str, exclude_content_patterns: List[str]) -> bool:
        if not exclude_content_patterns:
            return False
            
        filename = os.path.basename(file_path)
        for pattern in exclude_content_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
        
        return False
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            return "[Binary file]"
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"[Error reading file: {str(e)}]"