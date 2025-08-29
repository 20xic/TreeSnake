import os
from .utils import should_skip, should_exclude_content, read_file_content

def scan_project(root_dir, exclude_dirs=None, exclude_patterns=None, structure_only=False, 
                 exclude_content_dirs=None, exclude_content_patterns=None):
    """Сканирует проект и возвращает его структуру с содержимым"""
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_patterns is None:
        exclude_patterns = []
    if exclude_content_dirs is None:
        exclude_content_dirs = []
    if exclude_content_patterns is None:
        exclude_content_patterns = []
    
    result = []
    root_dir = os.path.normpath(root_dir)
    
    for current_dir, dirs, files in os.walk(root_dir):
        skip_content = False
        rel_path = os.path.relpath(current_dir, root_dir)
        for excl_content_dir in exclude_content_dirs:
            if rel_path.startswith(excl_content_dir) or excl_content_dir in current_dir.split(os.sep):
                skip_content = True
                break
        
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(current_dir, d), exclude_dirs, exclude_patterns)]
        
        if rel_path == '.':
            level = 0
        else:
            level = len(rel_path.split(os.sep))
        
        if level > 0:
            if level == 1:
                result.append(f"├── {os.path.basename(current_dir)}/")
            else:
                result.append(f"{'│   ' * (level-1)}├── {os.path.basename(current_dir)}/")
        
        if skip_content:
            if level == 0:
                result.append("└── [СОДЕРЖИМОЕ ДИРЕКТОРИИ ИСКЛЮЧЕНО]")
            else:
                result.append(f"{'│   ' * level}└── [СОДЕРЖИМОЕ ДИРЕКТОРИИ ИСКЛЮЧЕНО]")
            dirs[:] = []
            files = []
            continue
        
        for file in files:
            file_path = os.path.join(current_dir, file)
            if should_skip(file_path, exclude_dirs, exclude_patterns):
                continue
                
            if level == 0:
                result.append(f"├── {file}")
            else:
                result.append(f"{'│   ' * level}├── {file}")
            
            skip_file_content = should_exclude_content(file_path, exclude_content_patterns)
            
            if not structure_only and not skip_file_content:
                content, error = read_file_content(file_path)
                
                if error:
                    if level == 0:
                        result.append(f"│   └── {error}")
                    else:
                        result.append(f"{'│   ' * (level+1)}└── {error}")
                else:
                    if level == 0:
                        result.append("│   └── CONTENT:")
                    else:
                        result.append(f"{'│   ' * (level+1)}└── CONTENT:")
                    
                    for line in content.split('\n'):
                        if level == 0:
                            result.append(f"│       {line}")
                        else:
                            result.append(f"{'│   ' * (level+1)}    {line}")
                    
                    if level == 0:
                        result.append("│")
                    else:
                        result.append(f"{'│   ' * (level+1)}")
            else:
                if level == 0:
                    result.append("│   └── [СОДЕРЖИМОЕ ФАЙЛА ИСКЛЮЧЕНО]")
                else:
                    result.append(f"{'│   ' * (level+1)}└── [СОДЕРЖИМОЕ ФАЙЛА ИСКЛЮЧЕНО]")
    
    return '\n'.join(result)

def scan_project_llm(root_dir, exclude_dirs=None, exclude_patterns=None, structure_only=False,
                    exclude_content_dirs=None, exclude_content_patterns=None):
    """Сканирует проект и возвращает структуру в формате для LLM"""
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_patterns is None:
        exclude_patterns = []
    if exclude_content_dirs is None:
        exclude_content_dirs = []
    if exclude_content_patterns is None:
        exclude_content_patterns = []
    
    result = []
    root_dir = os.path.normpath(root_dir)
    
    for current_dir, dirs, files in os.walk(root_dir):
        skip_content = False
        rel_path = os.path.relpath(current_dir, root_dir)
        for excl_content_dir in exclude_content_dirs:
            if rel_path.startswith(excl_content_dir) or excl_content_dir in current_dir.split(os.sep):
                skip_content = True
                break
        
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(current_dir, d), exclude_dirs, exclude_patterns)]
        
        if rel_path == '.':
            level = 0
        else:
            level = len(rel_path.split(os.sep))
        
        indent = '  ' * level
        if level > 0:
            result.append(f"{indent}{os.path.basename(current_dir)}/")
        else:
            result.append(f"{os.path.basename(current_dir)}/")
        
        if skip_content:
            dirs[:] = []
            files = []
            continue
        
        for file in files:
            file_path = os.path.join(current_dir, file)
            if should_skip(file_path, exclude_dirs, exclude_patterns):
                continue
                
            file_indent = '  ' * (level + 1)
            result.append(f"{file_indent}{file}")
            
            skip_file_content = should_exclude_content(file_path, exclude_content_patterns)
            
            if not structure_only and not skip_file_content:
                content, error = read_file_content(file_path)
                
                if error:
                    result.append(f"{file_indent}  {error}")
                else:
                    for line in content.split('\n'):
                        result.append(f"{file_indent}  {line}")
    
    return '\n'.join(result)