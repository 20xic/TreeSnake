"""
TreeSnake 
Сканирует структуру проекта и сохраняет её вместе с содержимым файлов.
Использует специальные символы для наглядного отображения иерархии.
"""

import os
import argparse
import sys
import fnmatch

def should_skip(path, exclude_dirs, exclude_patterns):
    """Проверяет, нужно ли пропустить файл или директорию"""
    # Проверяем исключения директорий
    for excl_dir in exclude_dirs:
        if excl_dir in path.split(os.sep):
            return True
    
    # Проверяем исключения файлов с поддержкой шаблонов
    if os.path.isfile(path):
        filename = os.path.basename(path)
        # Проверяем соответствие шаблонам
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
        return None, "[Бинарный файл - содержимое пропущено]"
    except Exception as e:
        return None, f"[Ошибка чтения файла: {str(e)}]"

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
        # Проверяем, нужно ли исключить содержимое текущей директории
        skip_content = False
        rel_path = os.path.relpath(current_dir, root_dir)
        for excl_content_dir in exclude_content_dirs:
            if rel_path.startswith(excl_content_dir) or excl_content_dir in current_dir.split(os.sep):
                skip_content = True
                break
        
        # Фильтрация исключенных директорий
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(current_dir, d), exclude_dirs, exclude_patterns)]
        
        # Получаем относительный путь
        if rel_path == '.':
            level = 0
        else:
            level = len(rel_path.split(os.sep))
        
        # Добавляем запись для текущей директории
        if level > 0:
            # Используем специальные символы для отображения иерархии
            if level == 1:
                result.append(f"├── {os.path.basename(current_dir)}/")
            else:
                result.append(f"{'│   ' * (level-1)}├── {os.path.basename(current_dir)}/")
        
        # Если нужно пропустить содержимое директории, добавляем отметку и пропускаем файлы
        if skip_content:
            if level == 0:
                result.append("└── [СОДЕРЖИМОЕ ДИРЕКТОРИИ ИСКЛЮЧЕНО]")
            else:
                result.append(f"{'│   ' * level}└── [СОДЕРЖИМОЕ ДИРЕКТОРИИ ИСКЛЮЧЕНО]")
            # Очищаем списки, чтобы не обрабатывать вложенные элементы
            dirs[:] = []
            files = []
            continue
        
        # Обрабатываем файлы
        for file in files:
            file_path = os.path.join(current_dir, file)
            if should_skip(file_path, exclude_dirs, exclude_patterns):
                continue
                
            # Отображаем файлы с соответствующим уровнем вложенности
            if level == 0:
                result.append(f"├── {file}")
            else:
                result.append(f"{'│   ' * level}├── {file}")
            
            # Проверяем, нужно ли исключить содержимое этого файла
            skip_file_content = should_exclude_content(file_path, exclude_content_patterns)
            
            # Если не в режиме только структуры и не нужно исключать содержимое файла, читаем содержимое
            if not structure_only and not skip_file_content:
                content, error = read_file_content(file_path)
                
                if error:
                    if level == 0:
                        result.append(f"│   └── {error}")
                    else:
                        result.append(f"{'│   ' * (level+1)}└── {error}")
                else:
                    # Добавляем разделитель и содержимое
                    if level == 0:
                        result.append("│   └── CONTENT:")
                    else:
                        result.append(f"{'│   ' * (level+1)}└── CONTENT:")
                    
                    # Добавляем содержимое с отступом
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
                # Добавляем сообщение о пропущенном содержимом
                if level == 0:
                    result.append("│   └── [СОДЕРЖИМОЕ ФАЙЛА ИСКЛЮЧЕНО]")
                else:
                    result.append(f"{'│   ' * (level+1)}└── [СОДЕРЖИМОЕ ФАЙЛА ИСКЛЮЧЕНО]")
    
    return '\n'.join(result)

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
            
        # Проверяем, нужно ли исключить содержимое этого дополнительного файла
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

def main():
    parser = argparse.ArgumentParser(
        description='TreeSnake- Утилита для сканирования структуры проектов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  TreeSnake /path/to/project
  TreeSnake /path/to/project -o output.txt
  TreeSnake /path/to/project --exclude-dirs venv __pycache__ --exclude-files .gitignore *.pyc
  TreeSnake /path/to/project -s  # Только структура без содержимого
  TreeSnake /path/to/project --extra-files config.json README.md  # Добавить дополнительные файлы
  TreeSnake /path/to/project --exclude-content-dirs node_modules dist  # Исключить содержимое директорий
  TreeSnake /path/to/project --exclude-content-files *.txt *.md  # Исключить содержимое файлов по шаблону

Символы иерархии:
  ├── - элемент на уровне
  │   - продолжение родительского уровня
  └── - последний элемент на уровне
        """
    )
    
    parser.add_argument('root_dir', help='Корневая директория проекта для сканирования')
    parser.add_argument('-o', '--output', default='project_structure.txt', 
                       help='Имя выходного файла (по умолчанию: project_structure.txt)')
    parser.add_argument('-ed', '--exclude-dirs', nargs='+', default=[], 
                       help='Директории для исключения из сканирования')
    parser.add_argument('-ef', '--exclude-files', nargs='+', default=[], 
                       help='Файлы и шаблоны для исключения (например: .gitignore *.txt *.md)')
    parser.add_argument('-s', '--structure-only', action='store_true',
                       help='Выводить только структуру без содержимого файлов')
    parser.add_argument('-xf','--extra-files', nargs='+', default=[],
                       help='Дополнительные файлы для включения в отчет (вне структуры проекта)')
    parser.add_argument('-ecd', '--exclude-content-dirs', nargs='+', default=[],
                       help='Директории, содержимое которых нужно исключить (только структура)')
    parser.add_argument('-ecf', '--exclude-content-files', nargs='+', default=[],
                       help='Файлы и шаблоны, содержимое которых нужно исключить (например: *.txt *.md)')
    parser.add_argument('-v', '--version', action='version', version='TreeSnake 0.0.2')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.root_dir):
        print(f"Ошибка: Директория '{args.root_dir}' не существует!")
        sys.exit(1)
    
    # Проверяем существование дополнительных файлов
    missing_files = []
    for file_path in args.extra_files:
        if not os.path.isfile(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"Предупреждение: следующие дополнительные файлы не найдены: {', '.join(missing_files)}")
        print("Продолжение работы без этих файлов...")
    
    print("TreeSnake: Сканирование проекта...")
    content = scan_project(
        args.root_dir, 
        args.exclude_dirs, 
        args.exclude_files, 
        args.structure_only,
        args.exclude_content_dirs,
        args.exclude_content_files
    )
    
    # Добавляем дополнительные файлы, если указаны
    if args.extra_files:
        extra_content = add_extra_files(args.extra_files, args.structure_only, args.exclude_content_files)
        content += extra_content
    
    # Добавляем заголовок
    header = f"Структура проекта: {args.root_dir}\n"
    if args.extra_files:
        header += f"Дополнительные файлы: {', '.join(args.extra_files)}\n"
    if args.exclude_content_dirs:
        header += f"Директории с исключенным содержимым: {', '.join(args.exclude_content_dirs)}\n"
    if args.exclude_content_files:
        header += f"Файлы с исключенным содержимым: {', '.join(args.exclude_content_files)}\n"
    header += "=" * 60 + "\n\n"
    content = header + content
    
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Структура проекта сохранена в файл: {args.output}")
        print(f"Размер выходного файла: {os.path.getsize(args.output)} байт")
    except Exception as e:
        print(f"Ошибка при записи файла: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()