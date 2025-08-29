from .utils import should_exclude_content, read_file_content

def add_extra_files(extra_files, structure_only=False, exclude_content_patterns=None):
    """Добавляет дополнительные файлы вне структуры проекта"""
    if not extra_files:
        return ""
    
    if exclude_content_patterns is None:
        exclude_content_patterns = []
    
    result = ["\n\nДОПОЛНИТЕЛЬНЫЕ ФАЙЛЫ:"]
    result.append("=" * 40)
    
    for file_path in extra_files:
        if not os.path.isfile(file_path):
            result.append(f"\n{file_path} - [Файл не найден]")
            continue
            
        skip_content = should_exclude_content(file_path, exclude_content_patterns)
            
        result.append(f"\n├── {os.path.basename(file_path)} ({file_path})")
        
        if not structure_only and not skip_content:
            content, error = read_file_content(file_path)
            
            if error:
                result.append(f"│   └── {error}")
            else:
                result.append("│   └── CONTENT:")
                for line in content.split('\n'):
                    result.append(f"│       {line}")
                result.append("│")
        else:
            result.append("│   └── [Содержимое пропущено]")
    
    return '\n'.join(result)

def add_extra_files_llm(extra_files, structure_only=False, exclude_content_patterns=None):
    """Добавляет дополнительные файлы в формате для LLM"""
    if not extra_files:
        return ""
    
    if exclude_content_patterns is None:
        exclude_content_patterns = []
    
    result = ["\nExtra files:"]
    
    for file_path in extra_files:
        if not os.path.isfile(file_path):
            result.append(f"{file_path} [not found]")
            continue
            
        skip_content = should_exclude_content(file_path, exclude_content_patterns)
            
        result.append(f"{os.path.basename(file_path)}")
        
        if not structure_only and not skip_content:
            content, error = read_file_content(file_path)
            
            if error:
                result.append(f"  {error}")
            else:
                for line in content.split('\n'):
                    result.append(f"  {line}")
    
    return '\n'.join(result)