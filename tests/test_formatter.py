import json

import pytest

from core.formatter import (
    DefaultFormatter,
    JsonFormatter,
    JsonStringFormatter,
    LLMFormatter,
)
from models import Directory, File


@pytest.fixture
def simple_directory():
    return Directory(
        name="root",
        files=[
            File(name="main.py", content="print('hello')", size=14),
            File(name="empty.py", content="", size=0),
        ],
        subdirectories=[],
    )


@pytest.fixture
def nested_directory():
    return Directory(
        name="root",
        files=[File(name="main.py", content="print('hello')", size=14)],
        subdirectories=[
            Directory(
                name="core",
                files=[File(name="scanner.py", content="import os", size=9)],
                subdirectories=[
                    Directory(
                        name="utils",
                        files=[File(name="helper.py", content="pass", size=4)],
                        subdirectories=[],
                    )
                ],
            )
        ],
    )


class TestDefaultFormatter:
    def test_contains_root_dir(self, simple_directory):
        result = DefaultFormatter().format(simple_directory)
        assert "📁 root/" in result

    def test_contains_files(self, simple_directory):
        result = DefaultFormatter().format(simple_directory)
        assert "📄 main.py" in result
        assert "📄 empty.py" in result

    def test_contains_file_size(self, simple_directory):
        result = DefaultFormatter().format(simple_directory)
        assert "14 bytes" in result

    def test_contains_file_content(self, simple_directory):
        result = DefaultFormatter().format(simple_directory)
        assert "print('hello')" in result

    def test_empty_file_no_content_lines(self, simple_directory):
        result = DefaultFormatter().format(simple_directory)
        lines = result.splitlines()
        empty_file_line = next(i for i, l in enumerate(lines) if "empty.py" in l)  # noqa: E741
        next_line = (
            lines[empty_file_line + 1] if empty_file_line + 1 < len(lines) else ""
        )
        assert "📁" in next_line or "📄" in next_line or next_line == ""

    def test_nested_structure(self, nested_directory):
        result = DefaultFormatter().format(nested_directory)
        assert "📁 root/" in result
        assert "📁 core/" in result
        assert "📁 utils/" in result
        assert "📄 scanner.py" in result
        assert "📄 helper.py" in result

    def test_last_item_uses_corner(self, simple_directory):
        result = DefaultFormatter().format(simple_directory)
        assert "└──" in result

    def test_non_last_item_uses_branch(self, nested_directory):
        result = DefaultFormatter().format(nested_directory)
        assert "├──" in result

    def test_vertical_lines_for_nesting(self, nested_directory):
        result = DefaultFormatter().format(nested_directory)
        assert "│" in result


class TestLLMFormatter:
    def test_contains_file_path(self, simple_directory):
        result = LLMFormatter().format(simple_directory)
        assert "# root/main.py" in result

    def test_contains_file_content(self, simple_directory):
        result = LLMFormatter().format(simple_directory)
        assert "print('hello')" in result

    def test_contains_separator(self, simple_directory):
        result = LLMFormatter().format(simple_directory)
        assert "---" in result

    def test_empty_file_has_separator(self, simple_directory):
        result = LLMFormatter().format(simple_directory)
        lines = result.splitlines()
        empty_idx = next(i for i, l in enumerate(lines) if "empty.py" in l)  # noqa: E741
        assert lines[empty_idx + 1] == "---"

    def test_nested_paths(self, nested_directory):
        result = LLMFormatter().format(nested_directory)
        assert "# root/main.py" in result
        assert "# root/core/scanner.py" in result
        assert "# root/core/utils/helper.py" in result

    def test_no_square_brackets(self, nested_directory):
        result = LLMFormatter().format(nested_directory)
        assert "[" not in result
        assert "]" not in result

    def test_no_emojis(self, simple_directory):
        result = LLMFormatter().format(simple_directory)
        assert "📁" not in result
        assert "📄" not in result


class TestJsonFormatter:
    def test_returns_dict(self, simple_directory):
        result = JsonFormatter().format(simple_directory)
        assert isinstance(result, dict)

    def test_root_name(self, simple_directory):
        result = JsonFormatter().format(simple_directory)
        assert result["name"] == "root"

    def test_files_structure(self, simple_directory):
        result = JsonFormatter().format(simple_directory)
        assert len(result["files"]) == 2
        assert result["files"][0]["name"] == "main.py"
        assert result["files"][0]["content"] == "print('hello')"
        assert result["files"][0]["size"] == 14

    def test_nested_structure(self, nested_directory):
        result = JsonFormatter().format(nested_directory)
        assert result["subdirectories"][0]["name"] == "core"
        assert result["subdirectories"][0]["subdirectories"][0]["name"] == "utils"

    def test_empty_subdirectories(self, simple_directory):
        result = JsonFormatter().format(simple_directory)
        assert result["subdirectories"] == []


class TestJsonStringFormatter:
    def test_returns_string(self, simple_directory):
        result = JsonStringFormatter().format(simple_directory)
        assert isinstance(result, str)

    def test_valid_json(self, simple_directory):
        result = JsonStringFormatter().format(simple_directory)
        parsed = json.loads(result)
        assert parsed["name"] == "root"

    def test_custom_indent(self, simple_directory):
        result = JsonStringFormatter(indent=4).format(simple_directory)
        assert "    " in result

    def test_no_indent(self, simple_directory):
        result = JsonStringFormatter(indent=None).format(simple_directory)
        assert "\n" not in result

    def test_nested_structure(self, nested_directory):
        result = JsonStringFormatter().format(nested_directory)
        parsed = json.loads(result)
        assert parsed["subdirectories"][0]["name"] == "core"
