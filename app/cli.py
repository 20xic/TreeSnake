import os
import argparse
import sys
from .constants import ASCII_ART
from .scanner import scan_project, scan_project_llm
from .formatters import add_extra_files, add_extra_files_llm
from .utils import copy_to_clipboard

def main():
    if len(sys.argv) == 1:
        print(ASCII_ART)
        sys.exit(0)
    
    parser = argparse.ArgumentParser(
        description='TreeSnake- Утилита для сканирования структуры проектов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  TreeSnake /path/to/project
  TreeSnake /path/to/project -f output.txt
  TreeSnake /path/to/project --exclude-dirs venv __pycache__ --exclude-files .gitignore *.pyc
  TreeSnake /path/to/project -s  # Только структура без содержимого
  TreeSnake /path/to/project --extra-files config.json README.md  # Добавить дополнительные файлы
  TreeSnake /path/to/project --exclude-content-dirs node_modules dist  # Исключить содержимое директорий
  TreeSnake /path/to/project --exclude-content-files *.txt *.md  # Исключить содержимое файлов по шаблону
  TreeSnake /path/to/project --llm-mode  # Режим для LLM с экономией токенов

Символы иерархии:
  ├── - элемент на уровне
  │   - продолжение родительского уровня
  └── - последний элемент на уровне
        """
    )
    
    parser.add_argument('root_dir', nargs='?', help='Корневая директория проекта для сканирования')
    parser.add_argument('-f', '--file', dest='output_file', 
                       help='Имя выходного файла (если не указано, вывод в буфер обмена)')
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
    parser.add_argument('-lm','--llm-mode', action='store_true',
                       help='Режим для LLM с экономией токенов')
    parser.add_argument('-v', '--version', action='store_true', help='Показать версию программы')
    
    args = parser.parse_args()
    
    if args.version:
        print(ASCII_ART)
        print("TreeSnake 0.0.5")
        sys.exit(0)
    
    if args.root_dir is None:
        print("Ошибка: Не указана корневая директория проекта!")
        print("Используйте TreeSnake --help для просмотра справки")
        sys.exit(1)
    
    if not os.path.isdir(args.root_dir):
        print(f"Ошибка: Директория '{args.root_dir}' не существует!")
        sys.exit(1)
    
    missing_files = []
    for file_path in args.extra_files:
        if not os.path.isfile(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"Предупреждение: следующие дополнительные файлы не найдены: {', '.join(missing_files)}")
        print("Продолжение работы без этих файлов...")
    
    print("TreeSnake: Сканирование проекта...")
    
    if args.llm_mode:
        content = scan_project_llm(
            args.root_dir, 
            args.exclude_dirs, 
            args.exclude_files, 
            args.structure_only,
            args.exclude_content_dirs,
            args.exclude_content_files
        )
        
        if args.extra_files:
            extra_content = add_extra_files_llm(args.extra_files, args.structure_only, args.exclude_content_files)
            content += extra_content
    else:
        content = scan_project(
            args.root_dir, 
            args.exclude_dirs, 
            args.exclude_files, 
            args.structure_only,
            args.exclude_content_dirs,
            args.exclude_content_files
        )
        
        if args.extra_files:
            extra_content = add_extra_files(args.extra_files, args.structure_only, args.exclude_content_files)
            content += extra_content
        
        header = f"Структура проекта: {args.root_dir}\n"
        if args.extra_files:
            header += f"Дополнительные файлы: {', '.join(args.extra_files)}\n"
        if args.exclude_content_dirs:
            header += f"Директории с исключенным содержимым: {', '.join(args.exclude_content_dirs)}\n"
        if args.exclude_content_files:
            header += f"Файлы с исключенным содержимым: {', '.join(args.exclude_content_files)}\n"
        header += "=" * 60 + "\n\n"
        content = header + content
    
    if args.output_file:
        try:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Структура проекта сохранена в файл: {args.output_file}")
            print(f"Размер выходного файла: {os.path.getsize(args.output_file)} байт")
        except Exception as e:
            print(f"Ошибка при записи файла: {str(e)}")
            sys.exit(1)
    else:
        copy_to_clipboard(content)