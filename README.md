# TreeSnake

**TreeSnake** — утилита для сканирования и документирования структуры проектов с сохранением содержимого файлов.
**TreeSnake** — A utility for scanning and documenting project structure while preserving file contents.

## Назначение / Purpose

***TreeSnake создает подробную текстовую документацию вашего проекта, включая:***

* Иерархическую структуру директорий и файлов
* Содержимое всех файлов (кроме исключенных)
* Визуально понятное представление вложенности

***TreeSnake creates detailed text documentation of your project including:***

* Hierarchical structure of directories and files
* Content of all files (except excluded ones)
* Visually clear representation of nesting

## Установка / Installation

1. Клонируйте репозиторий:
```
git clone https://github.com/yourusername/treesnake.git
cd treesnake
```
2. Установите зависимости
```
pip install -r requirements
```


1. Clone the repository:
```
git clone https://github.com/yourusername/treesnake.git
cd treesnake
```
2. Install dependencies
```
pip install -r requirements
```

## Сборка / Build
```
pip install -r requirements.txt
pyinstaller --onefile --console --name treesnake main.py
```

## Использование / Usage

#### Базовое использование / Basic usage
```
python treesnake.py /path/to/your/project
```
#### Расширенное использование / Advanced usage
```
python treesnake.py /path/to/your/project
-o custom_output.txt
--exclude-dirs venv __pycache__ node_modules
--exclude-files .gitignore .env config.ini
```
#### Параметры командной строки / Command line parameters


| Параметр / Parameter | Описание / Description                                                                               | По умолчанию / Default      |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `root_dir`                   | Корневая директория проекта / Project root directory (required)                     | -                                      |
| `-o, --output`               | Имя выходного файла / Output filename                                                       | `project_structure.txt`                |
| `-ed, --exclude-dirs`             | Список директорий для исключения / Directories to exclude                       | Пустой список / Empty list |
| `-ef, --exclude-files`            | Список файлов для исключения содержимого / Files to exclude content from | Пустой список / Empty list |
|`-s, --structure-only`| Выводить только структуру без содержимого файлов/ Show project structure only    | Пустой список / Empty list
|`-xf, --extra-files`| Дополнительные файлы для включения в отчет (вне структуры проекта)| Пустой список / Empty list
|`-ecd, --exclude-content-dirs`| Директории, содержимое которых нужно исключить (только структура)| Пустой список / Empty list
|`-ecf, --exclude-content-files`| Файлы и шаблоны, содержимое которых нужно исключить (например: *.txt *.md)| Пустой список / Empty list
| `-v, --version`              | Показать версию утилиты / Show utility version                                          | -|


#### Пример вывода / Example Output

Структура проекта: /path/to/project
```
===================================================

├── app/
│   ├── core/
│   │   ├── config.py
│   │   │   └── CONTENT:
│   │   │       DB_HOST = "localhost"
│   │   │       DB_PORT = 5432
│   │   │
│   │   └── logger.py
│   │       └── CONTENT:
│   │           import logging
│   │
│   │           def setup_logger():
│   │               logging.basicConfig(level=logging.INFO)
│   │
│   │
│   └── main.py
│       └── CONTENT:
│           from fastapi import FastAPI
│
│           app = FastAPI()
│
│
```

#### Особенности / Features

* **Визуальная иерархия** / Visual hierarchy: Использует символы `├──`, `│` и `└──` для наглядного отображения структуры
* **Гибкие исключения** / Flexible exclusions: Возможность исключать директории и файлы из сканирования
* **Обработка ошибок** / Error handling: Корректная обработка бинарных файлов и файлов с ошибками доступа
* **Кодировка UTF-8** / UTF-8 encoding: Поддержка различных символов и языков


#### Ограничения / Limitations

* Не рекурсирует в символические ссылки (как и стандартный os.walk)
* Бинарные файлы пропускаются (содержимое не отображается)
* Не анализирует зависимости или импорты внутри кода
* Does not recurse into symbolic links (like standard os.walk)
* Binary files are skipped (content is not displayed)
* Does not analyze dependencies or imports within code
