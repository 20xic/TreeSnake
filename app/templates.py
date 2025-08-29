import os
import json
from pathlib import Path
from typing import Dict, Any

class TemplateManager:
    def __init__(self):
        self.config_dir = Path.home() / ".treesnake"
        self.templates_file = self.config_dir / "templates.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Создает директорию для конфигурационных файлов если она не существует"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.templates_file.exists():
            self._save_templates({})

    def _load_templates(self) -> Dict[str, Any]:
        """Загружает шаблоны из файла"""
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_templates(self, templates: Dict[str, Any]):
        """Сохраняет шаблоны в файл"""
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)

    def create_template(self, name: str, options: Dict[str, Any]):
        """Создает новый шаблон"""
        templates = self._load_templates()
        templates[name] = options
        self._save_templates(templates)

    def get_template(self, name: str) -> Dict[str, Any]:
        """Получает шаблон по имени"""
        templates = self._load_templates()
        return templates.get(name)

    def list_templates(self) -> list:
        """Возвращает список всех шаблонов"""
        templates = self._load_templates()
        return list(templates.keys())

    def delete_template(self, name: str):
        """Удаляет шаблон"""
        templates = self._load_templates()
        if name in templates:
            del templates[name]
            self._save_templates(templates)

    def get_default_template(self) -> str:
        """Получает шаблон по умолчанию"""
        templates = self._load_templates()
        return templates.get('__default__')

    def set_default_template(self, name: str):
        """Устанавливает шаблон по умолчанию"""
        templates = self._load_templates()
        if name in templates:
            templates['__default__'] = name
            self._save_templates(templates)