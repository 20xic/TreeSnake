import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.domain import Template


class TemplateManager:
    def __init__(self):
        self.config_dir = Path.home() / ".treesnake"
        self.templates_file = self.config_dir / "templates.json"
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.templates_file.exists():
            self._save_templates({})
    
    def _load_templates(self) -> Dict[str, Any]:
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_templates(self, templates: Dict[str, Any]):
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)
    
    def create_template(self, name: str, template: Template):
        templates = self._load_templates()
        template_dict = {
            'exclude_dirs': template.exclude_dirs,
            'exclude_patterns': template.exclude_patterns,
            'exclude_content_dirs': template.exclude_content_dirs,
            'exclude_content_patterns': template.exclude_content_patterns,
            'structure_only': template.structure_only,
            'llm_mode': template.llm_mode,
            'extra_files': template.extra_files,
        }
        templates[name] = template_dict
        self._save_templates(templates)
    
    def get_template(self, name: str) -> Optional[Template]:
        templates = self._load_templates()
        template_data = templates.get(name)
        if template_data:
            return Template(
                name=name,
                exclude_dirs=template_data.get('exclude_dirs', []),
                exclude_patterns=template_data.get('exclude_patterns', []),
                exclude_content_dirs=template_data.get('exclude_content_dirs', []),
                exclude_content_patterns=template_data.get('exclude_content_patterns', []),
                structure_only=template_data.get('structure_only', False),
                llm_mode=template_data.get('llm_mode', False),
                extra_files=template_data.get('extra_files', []),
            )
        return None
    
    def list_templates(self) -> list:
        templates = self._load_templates()
        return [name for name in templates.keys() if name != '__default__']
    
    def delete_template(self, name: str):
        templates = self._load_templates()
        if name in templates:
            del templates[name]
            if templates.get('__default__') == name:
                del templates['__default__']
            self._save_templates(templates)
    
    def get_default_template(self) -> Optional[str]:
        templates = self._load_templates()
        return templates.get('__default__')
    
    def set_default_template(self, name: str):
        templates = self._load_templates()
        if name in templates:
            templates['__default__'] = name
            self._save_templates(templates)