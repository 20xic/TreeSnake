import os
import fnmatch
import pyperclip

def should_skip(path, exclude_dirs, exclude_patterns):
    """Проверяет, нужно ли пропустить файл или директорию"""
    for excl_dir in exclude_dirs:
        if excl_dir in path.split(os.sep):
            return True
    
    if os.path.isfile(path):
        filename = os.path.basename(path)
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
    
    return False

def should_exclude_content(file_path, exclude_content_patterns):
    """Проверяет, нужно ли исключить содержимое файла"""
    if not exclude_content_patterns:
        return False
        
    filename = os.path.basename(file_path)
    for pattern in exclude_content_patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True
    
    return False

def read_file_content(file_path):
    """Читает содержимое файла с обработкой ошибок"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), None
    except UnicodeDecodeError:
        return None, "[Бинарный файл]"
    except Exception as e:
        return None, f"[Ошибка: {str(e)}]"

def copy_to_clipboard(content):
    """Копирует содержимое в буфер обмена"""
    try:
        pyperclip.copy(content)
        print("Содержимое скопировано в буфер обмена!")
    except Exception as e:
        print(f"Ошибка при копировании в буфер обмена: {str(e)}")
        print("Убедитесь, что у вас установлены необходимые зависимости для работы с буфером обмена")
        raise

def create_empty_file(file_path, content=""):
    """Создает пустой файл"""
    try:
        # Создаем директории если их нет
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Файл создан: {file_path}")
        return True
    except Exception as e:
        print(f"Ошибка при создании файла {file_path}: {str(e)}")
        return False