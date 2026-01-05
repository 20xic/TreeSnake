import os
import sys
import argparse

from src.core.logger import logger
from src.cli.art import ASCII_ART
from src.scanner import Scanner
from src.formatter import TreeFormatter, LLMFormatter
from src.core.template_manager import TemplateManager
from src.domain import Template, ScannerConfig



class TreeSnakeCLI:
    def __init__(self):
        self.scanner = Scanner()
        self.template_manager = TemplateManager()
        
    def run(self):
        if len(sys.argv) == 1:
            print(ASCII_ART)
            sys.exit(0)

        parser = self._create_parser()
        args = parser.parse_args()
        
        # Обработка версии
        if args.version:
            self._show_version()
            sys.exit(0)
        
        # Обработка команд шаблонов
        if args.create_template:
            self._handle_create_template(args)
            return
        elif args.list_templates:
            self._handle_list_templates()
            return
        elif args.delete_template:
            self._handle_delete_template(args.delete_template)
            return
        elif args.set_default_template:
            self._handle_set_default_template(args.set_default_template)
            return
        
        # Обработка основного сканирования
        if args.root_dir:
            self._handle_scan(args)
        else:
            print("Ошибка: Не указана корневая директория проекта!")
            print("Используйте --help для просмотра справки")
            sys.exit(1)
    
    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description='TreeSnake - Утилита для сканирования структуры проектов'
        )
        
        # Основные аргументы
        parser.add_argument('root_dir', nargs='?', help='Корневая директория проекта')
        parser.add_argument('-f', '--file', dest='output_file', 
                          help='Имя выходного файла')
        parser.add_argument('-ed', '--exclude-dirs', nargs='+', default=[], 
                          help='Директории для исключения')
        parser.add_argument('-ef', '--exclude-files', nargs='+', default=[], 
                          help='Файлы для исключения')
        parser.add_argument('-s', '--structure-only', action='store_true',
                          help='Только структура без содержимого')
        parser.add_argument('-lm', '--llm-mode', action='store_true',
                          help='Режим для LLM')
        parser.add_argument('-v', '--version', action='store_true', 
                          help='Показать версию')
        parser.add_argument('-t', '--template', help='Использовать шаблон')
        parser.add_argument('-ecd', '--exclude-content-dirs', nargs='+', default=[],
                          help='Директории, содержимое которых нужно исключить')
        parser.add_argument('-ecf', '--exclude-content-files', nargs='+', default=[],
                          help='Файлы, содержимое которых нужно исключить')
        
        # Управление шаблонами
        parser.add_argument('--create-template', help='Создать шаблон')
        parser.add_argument('--list-templates', action='store_true', 
                          help='Показать шаблоны')
        parser.add_argument('--delete-template', help='Удалить шаблон')
        parser.add_argument('--set-default-template', 
                          help='Установить шаблон по умолчанию')
        
        return parser
    
    def _handle_scan(self, args):
        # Получаем конфигурацию сканирования
        config = self._build_config(args)
        
        # Сканируем проект
        logger.info("TreeSnake: Сканирование проекта...")
        directory_tree = self.scanner.scan(args.root_dir, config)
        
        # Выбираем форматтер на основе llm_mode
        if config.llm_mode:
            formatter = LLMFormatter()
        else:
            formatter = TreeFormatter()
        
        # Форматируем результат
        result = formatter.format_directory(directory_tree)
        
        # Добавляем заголовок для не-LLM режима
        if not config.llm_mode:
            header = self._build_header(args.root_dir, config)
            result = header + result
        
        # Сохраняем или выводим результат
        if args.output_file:
            self._save_to_file(args.output_file, result)
        else:
            self._copy_to_clipboard(result)
    
    def _build_config(self, args) -> ScannerConfig:
        """Строит конфигурацию сканирования из аргументов и шаблона"""
        # Настройки по умолчанию
        exclude_dirs = []
        exclude_patterns = []
        exclude_content_dirs = []
        exclude_content_patterns = []
        structure_only = False
        llm_mode = False
        
        # Загружаем шаблон если указан
        if args.template:
            template = self.template_manager.get_template(args.template)
            if template:
                logger.info(f"Используется шаблон: {args.template}")
                # Используем настройки из шаблона
                exclude_dirs = template.exclude_dirs.copy()
                exclude_patterns = template.exclude_patterns.copy()
                exclude_content_dirs = template.exclude_content_dirs.copy()
                exclude_content_patterns = template.exclude_content_patterns.copy()
                structure_only = template.structure_only
                llm_mode = template.llm_mode
            else:
                logger.error(f"Шаблон '{args.template}' не найден!")
                sys.exit(1)
        else:
            # Проверяем шаблон по умолчанию
            default_template_name = self.template_manager.get_default_template()
            if default_template_name:
                template = self.template_manager.get_template(default_template_name)
                if template:
                    logger.info(f"Используется шаблон по умолчанию: {default_template_name}")
                    exclude_dirs = template.exclude_dirs.copy()
                    exclude_patterns = template.exclude_patterns.copy()
                    exclude_content_dirs = template.exclude_content_dirs.copy()
                    exclude_content_patterns = template.exclude_content_patterns.copy()
                    structure_only = template.structure_only
                    llm_mode = template.llm_mode
        
        # Аргументы командной строки имеют приоритет над шаблоном
        if args.exclude_dirs:
            exclude_dirs = args.exclude_dirs
        if args.exclude_files:
            exclude_patterns = args.exclude_files
        if args.exclude_content_dirs:
            exclude_content_dirs = args.exclude_content_dirs
        if args.exclude_content_files:
            exclude_content_patterns = args.exclude_content_files
        if args.structure_only:
            structure_only = True
        if args.llm_mode:
            llm_mode = True
        
        return ScannerConfig(
            exclude_dirs=exclude_dirs,
            exclude_patterns=exclude_patterns,
            exclude_content_dirs=exclude_content_dirs,
            exclude_content_patterns=exclude_content_patterns,
            structure_only=structure_only,
            llm_mode=llm_mode
        )
    
    def _build_header(self, root_dir: str, config: ScannerConfig) -> str:
        """Создает заголовок для результата"""
        header_lines = [
            f"Структура проекта: {root_dir}",
            f"Директории исключены: {', '.join(config.exclude_dirs) if config.exclude_dirs else 'нет'}",
            f"Файлы исключены: {', '.join(config.exclude_patterns) if config.exclude_patterns else 'нет'}",
        ]
        
        if config.exclude_content_dirs:
            header_lines.append(
                f"Директории с исключенным содержимым: {', '.join(config.exclude_content_dirs)}"
            )
        
        if config.exclude_content_patterns:
            header_lines.append(
                f"Файлы с исключенным содержимым: {', '.join(config.exclude_content_patterns)}"
            )
        
        if config.structure_only:
            header_lines.append("Только структура (без содержимого файлов)")
        
        if config.llm_mode:
            header_lines.append("Режим LLM (компактный формат)")
        
        header = "\n".join(header_lines) + "\n"
        header += "=" * 60 + "\n\n"
        return header
    
    def _save_to_file(self, filename: str, content: str):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Структура проекта сохранена в файл: {filename}")
            logger.info(f"Размер выходного файла: {os.path.getsize(filename)} байт")
        except Exception as e:
            logger.error(f"Ошибка при записи файла: {str(e)}")
            sys.exit(1)
    
    def _copy_to_clipboard(self, content: str):
        try:
            import pyperclip
            pyperclip.copy(content)
            logger.info("Содержимое скопировано в буфер обмена!")
        except ImportError:
            logger.warning("pyperclip не установлен, вывод в консоль:")
            print(content)
        except Exception as e:
            logger.error(f"Ошибка при копировании в буфер обмена: {str(e)}")
            print("Вывод в консоль:")
            print(content)
    
    def _show_version(self):
        from src import __version__
        print(f"TreeSnake v{__version__}")
    
    def _handle_create_template(self, args):
        # Создаем шаблон из аргументов
        template = Template(
            name=args.create_template,
            exclude_dirs=args.exclude_dirs,
            exclude_patterns=args.exclude_files,
            exclude_content_dirs=args.exclude_content_dirs,
            exclude_content_patterns=args.exclude_content_files,
            structure_only=args.structure_only,
            llm_mode=args.llm_mode,
            extra_files=[]
        )
        self.template_manager.create_template(args.create_template, template)
        logger.info(f"Шаблон '{args.create_template}' успешно создан!")
    
    def _handle_list_templates(self):
        templates = self.template_manager.list_templates()
        default_template = self.template_manager.get_default_template()
        
        if not templates:
            print("Нет сохраненных шаблонов.")
        else:
            print("Доступные шаблоны:")
            for template in templates:
                if template == default_template:
                    print(f"  {template} (по умолчанию)")
                else:
                    print(f"  {template}")
    
    def _handle_delete_template(self, name: str):
        self.template_manager.delete_template(name)
        logger.info(f"Шаблон '{name}' успешно удален!")
    
    def _handle_set_default_template(self, name: str):
        template = self.template_manager.get_template(name)
        if template:
            self.template_manager.set_default_template(name)
            logger.info(f"Шаблон '{name}' установлен по умолчанию!")
        else:
            logger.error(f"Шаблон '{name}' не найден!")
            sys.exit(1)


def main():
    cli = TreeSnakeCLI()
    cli.run()


if __name__ == "__main__":
    main()