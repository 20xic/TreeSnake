"""
TreeSnake 
Сканирует структуру проекта и сохраняет её вместе с содержимым файлов.
Использует специальные символы для наглядного отображения иерархии.
"""

import os
import argparse
import sys

def should_skip(path, exclude_dirs, exclude_files):
    """Проверяет, нужно ли пропустить файл или директорию"""
    # Проверяем исключения директорий
    for excl_dir in exclude_dirs:
        if excl_dir in path.split(os.sep):
            return True
    
    # Проверяем исключения файлов
    if os.path.isfile(path):
        filename = os.path.basename(path)
        if filename in exclude_files:
            return True
    
    return False

def scan_project(root_dir, exclude_dirs=None, exclude_files=None):
    """Сканирует проект и возвращает его структуру с содержимым"""
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_files is None:
        exclude_files = []
    
    result = []
    root_dir = os.path.normpath(root_dir)
    
    for current_dir, dirs, files in os.walk(root_dir):
        # Фильтрация исключенных директорий
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(current_dir, d), exclude_dirs, exclude_files)]
        
        # Получаем относительный путь
        rel_path = os.path.relpath(current_dir, root_dir)
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
        
        # Обрабатываем файлы
        for file in files:
            file_path = os.path.join(current_dir, file)
            if should_skip(file_path, exclude_dirs, exclude_files):
                continue
                
            # Отображаем файлы с соответствующим уровнем вложенности
            if level == 0:
                result.append(f"├── {file}")
            else:
                result.append(f"{'│   ' * level}├── {file}")
            
            # Читаем содержимое файла если он не в исключениях
            if file not in exclude_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
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
                except UnicodeDecodeError:
                    if level == 0:
                        result.append("│   └── [Бинарный файл - содержимое пропущено]")
                    else:
                        result.append(f"{'│   ' * (level+1)}└── [Бинарный файл - содержимое пропущено]")
                except Exception as e:
                    if level == 0:
                        result.append(f"│   └── [Ошибка чтения файла: {str(e)}]")
                    else:
                        result.append(f"{'│   ' * (level+1)}└── [Ошибка чтения файла: {str(e)}]")
    
    return '\n'.join(result)

def main():
    parser = argparse.ArgumentParser(
        description='TreeSnake- Утилита для сканирования структуры проектов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  TreeSnake /path/to/project
  TreeSnake /path/to/project -o output.txt
  TreeSnake /path/to/project --exclude-dirs venv __pycache__ --exclude-files .gitignore

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
                    help='Файлы для исключения содержимого (только имена)')
    parser.add_argument('-v', '--version', action='version', version='TreeSnake 1.0')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.root_dir):
        print(f"Ошибка: Директория '{args.root_dir}' не существует!")
        sys.exit(1)
    
    print("TreeSnake: Сканирование проекта...")
    content = scan_project(args.root_dir, args.exclude_dirs, args.exclude_files)
    
    # Добавляем заголовок
    header = f"Структура проекта: {args.root_dir}\n"
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