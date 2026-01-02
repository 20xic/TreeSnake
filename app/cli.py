import os
import argparse
import sys
from .constants import ASCII_ART
from .scanner import scan_project, scan_project_llm
from .formatters import add_extra_files, add_extra_files_llm
from .utils import copy_to_clipboard, create_empty_file
from .templates import TemplateManager

def main():
    if len(sys.argv) == 1:
        print(ASCII_ART)
        sys.exit(0)
    
    # Основной парсер
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
  TreeSnake --template my_template /path/to/project  # Использовать шаблон
  TreeSnake --create-template my_template --exclude-dirs venv --structure-only  # Создать шаблон
  TreeSnake --list-templates  # Показать все шаблоны
  TreeSnake --set-default-template my_template  # Установить шаблон по умолчанию
  TreeSnake --delete-template my_template  # Удалить шаблон
  TreeSnake -cf new.txt /path/to/project  # Создать файл и просканировать проект
  TreeSnake -cf new.txt  # Создать файл в текущей директории

Символы иерархии:
  ├── - элемент на уровне
  │   - продолжение родительского уровня
  └── - последний элемент на уровне
        """
    )
    
    # Основные аргументы
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
    parser.add_argument('-t', '--template', help='Использовать указанный шаблон')
    
    # Аргументы для управления шаблонами
    parser.add_argument('--create-template', help='Создать новый шаблон с указанным именем')
    parser.add_argument('--ct-exclude-dirs', nargs='+', default=[], 
                       help='Директории для исключения из сканирования (для создания шаблона)')
    parser.add_argument('--ct-exclude-files', nargs='+', default=[], 
                       help='Файлы и шаблоны для исключения (для создания шаблона)')
    parser.add_argument('--ct-structure-only', action='store_true',
                       help='Выводить только структуру без содержимого файлов (для создания шаблона)')
    parser.add_argument('--ct-extra-files', nargs='+', default=[],
                       help='Дополнительные файлы для включения в отчет (для создания шаблона)')
    parser.add_argument('--ct-exclude-content-dirs', nargs='+', default=[],
                       help='Директории, содержимое которых нужно исключить (для создания шаблона)')
    parser.add_argument('--ct-exclude-content-files', nargs='+', default=[],
                       help='Файлы и шаблоны, содержимое которых нужно исключить (для создания шаблона)')
    parser.add_argument('--ct-llm-mode', action='store_true',
                       help='Режим для LLM с экономией токенов (для создания шаблона)')
    
    parser.add_argument('--list-templates', action='store_true', help='Показать все шаблоны')
    parser.add_argument('--delete-template', help='Удалить шаблон с указанным именем')
    parser.add_argument('--set-default-template', help='Установить шаблон по умолчанию')

    # аргумент для создания файла
    parser.add_argument('-cf', '--create-file', dest='create_file', metavar='FILEPATH',
                       help='Создать пустой файл по указанному пути')
    
    args = parser.parse_args()
    
    if args.version:
        print(ASCII_ART)
        print(5*"\t"+" v0.1.2")
        sys.exit(0)
    
    # Обработка команд шаблонов
    template_manager = TemplateManager()
    
    if args.create_template:
        # Создаем шаблон из переданных аргументов
        template_options = {
            'exclude_dirs': args.ct_exclude_dirs,
            'exclude_files': args.ct_exclude_files,
            'structure_only': args.ct_structure_only,
            'extra_files': args.ct_extra_files,
            'exclude_content_dirs': args.ct_exclude_content_dirs,
            'exclude_content_files': args.ct_exclude_content_files,
            'llm_mode': args.ct_llm_mode
        }
        template_manager.create_template(args.create_template, template_options)
        print(f"Шаблон '{args.create_template}' успешно создан!")
        sys.exit(0)
        
    elif args.list_templates:
        templates = template_manager.list_templates()
        default_template = template_manager.get_default_template()
        
        if not templates:
            print("Нет сохраненных шаблонов.")
        else:
            print("Доступные шаблоны:")
            for template in templates:
                if template == default_template:
                    print(f"  {template} (по умолчанию)")
                else:
                    print(f"  {template}")
        sys.exit(0)
        
    elif args.delete_template:
        template_manager.delete_template(args.delete_template)
        print(f"Шаблон '{args.delete_template}' успешно удален!")
        sys.exit(0)
        
    elif args.set_default_template:
        if template_manager.get_template(args.set_default_template):
            template_manager.set_default_template(args.set_default_template)
            print(f"Шаблон '{args.set_default_template}' установлен по умолчанию!")
        else:
            print(f"Шаблон '{args.set_default_template}' не найден!")
        sys.exit(0)
    
    # ОБРАБОТКА СОЗДАНИЯ ФАЙЛА (ДОЛЖНА БЫТЬ ДО ПРОВЕРКИ root_dir)
    if args.create_file:
        # Определяем базовую директорию для создания файла
        if args.root_dir:
            # Если указана корневая директория, создаем файл в ней
            base_dir = args.root_dir
            # Проверяем, существует ли директория
            if not os.path.isdir(base_dir):
                print(f"Ошибка: Директория '{base_dir}' не существует!")
                sys.exit(1)
        else:
            # Если корневая директория не указана, используем текущую
            base_dir = os.getcwd()
        
        # Обрабатываем путь к файлу
        target_file = args.create_file
        
        # Убираем начальные ./ или .\ если они есть
        if target_file.startswith('./') or target_file.startswith('.\\'):
            target_file = target_file[2:]
        
        # Формируем полный путь
        file_path = os.path.join(base_dir, target_file)
        
        # Создаем файл
        success = create_empty_file(file_path)
        if not success:
            sys.exit(1)
        
        # Если не указаны аргументы для сканирования, просто выходим
        if not args.output_file and not any([args.exclude_dirs, args.exclude_files, 
                                           args.structure_only, args.extra_files,
                                           args.exclude_content_dirs, args.exclude_content_files,
                                           args.llm_mode, args.template]):
            sys.exit(0)
    
    # Обработка основного режима сканирования
    if args.root_dir is None:
        print("Ошибка: Не указана корневая директория проекта!")
        print("Используйте TreeSnake --help для просмотра справки")
        sys.exit(1)
    
    # Загрузка настроек из шаблона если указан
    template_options = {}
    if args.template:
        template_options = template_manager.get_template(args.template)
        if not template_options:
            print(f"Ошибка: Шаблон '{args.template}' не найден!")
            sys.exit(1)
        print(f"Используется шаблон: {args.template}")
    else:
        # Проверяем есть ли шаблон по умолчанию
        default_template_name = template_manager.get_default_template()
        if default_template_name:
            template_options = template_manager.get_template(default_template_name)
            if template_options:
                print(f"Используется шаблон по умолчанию: {default_template_name}")
    
    # Объединяем настройки из шаблона с аргументами командной строки
    # Аргументы командной строки имеют приоритет над настройками шаблона
    if template_options:
        exclude_dirs = args.exclude_dirs or template_options.get('exclude_dirs', [])
        exclude_files = args.exclude_files or template_options.get('exclude_files', [])
        structure_only = args.structure_only or template_options.get('structure_only', False)
        extra_files = args.extra_files or template_options.get('extra_files', [])
        exclude_content_dirs = args.exclude_content_dirs or template_options.get('exclude_content_dirs', [])
        exclude_content_files = args.exclude_content_files or template_options.get('exclude_content_files', [])
        llm_mode = args.llm_mode or template_options.get('llm_mode', False)
    else:
        exclude_dirs = args.exclude_dirs
        exclude_files = args.exclude_files
        structure_only = args.structure_only
        extra_files = args.extra_files
        exclude_content_dirs = args.exclude_content_dirs
        exclude_content_files = args.exclude_content_files
        llm_mode = args.llm_mode
    
    if not os.path.isdir(args.root_dir):
        print(f"Ошибка: Директория '{args.root_dir}' не существует!")
        sys.exit(1)
    
    missing_files = []
    for file_path in extra_files:
        if not os.path.isfile(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"Предупреждение: следующие дополнительные файлы не найдены: {', '.join(missing_files)}")
        print("Продолжение работы без этих файлов...")
    
    print("TreeSnake: Сканирование проекта...")
    
    if llm_mode:
        content = scan_project_llm(
            args.root_dir, 
            exclude_dirs, 
            exclude_files, 
            structure_only,
            exclude_content_dirs,
            exclude_content_files
        )
        
        if extra_files:
            extra_content = add_extra_files_llm(extra_files, structure_only, exclude_content_files)
            content += extra_content
    else:
        content = scan_project(
            args.root_dir, 
            exclude_dirs, 
            exclude_files, 
            structure_only,
            exclude_content_dirs,
            exclude_content_files
        )
        
        if extra_files:
            extra_content = add_extra_files(extra_files, structure_only, exclude_content_files)
            content += extra_content
        
        header = f"Структура проекта: {args.root_dir}\n"
        if extra_files:
            header += f"Дополнительные файлы: {', '.join(extra_files)}\n"
        if exclude_content_dirs:
            header += f"Директории с исключенным содержимым: {', '.join(exclude_content_dirs)}\n"
        if exclude_content_files:
            header += f"Файлы с исключенным содержимым: {', '.join(exclude_content_files)}\n"
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