import json
import xml.etree.ElementTree as ET

import pytest

from core.formatter import (
    DefaultFormatter,
    JsonFormatter,
    JsonStringFormatter,
    LLMFormatter,
    XmlFormatter,
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
        empty_file_line = next(i for i, l in enumerate(lines) if "empty.py" in l)
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
        empty_idx = next(i for i, l in enumerate(lines) if "empty.py" in l)
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


class TestXmlFormatter:
    def test_valid_xml_with_declaration(self, nested_directory):
        result = XmlFormatter().format(nested_directory)
        assert result.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        root = ET.fromstring(result)
        assert root.tag == "project"
        assert root.get("name") == "root"

    def test_files_carry_name_path_size(self, simple_directory):
        root = ET.fromstring(XmlFormatter().format(simple_directory))
        main = root.find("file[@name='main.py']")
        assert main is not None
        assert main.get("path") == "root/main.py"
        assert main.get("size") == "14"

    def test_content_preserved_verbatim(self, simple_directory):
        root = ET.fromstring(XmlFormatter().format(simple_directory))
        main = root.find("file[@name='main.py']")
        assert main.text.strip() == "print('hello')"

    def test_empty_file_is_self_closing(self, simple_directory):
        result = XmlFormatter().format(simple_directory)
        assert '<file name="empty.py" path="root/empty.py" size="0" />' in result

    def test_nested_directories(self, nested_directory):
        root = ET.fromstring(XmlFormatter().format(nested_directory))
        core = root.find("directory[@name='core']")
        assert core is not None
        utils = core.find("directory[@name='utils']")
        assert utils is not None
        helper = utils.find("file[@name='helper.py']")
        assert helper.get("path") == "root/core/utils/helper.py"

    def test_empty_directory_is_self_closing(self):
        directory = Directory(
            name="root",
            files=[],
            subdirectories=[Directory(name="dist", files=[], subdirectories=[])],
        )
        result = XmlFormatter().format(directory)
        assert '<directory name="dist" />' in result

    def test_content_is_not_entity_escaped(self):
        directory = Directory(
            name="root",
            files=[File(name="a.html", content="<b>x & y</b>", size=12)],
            subdirectories=[],
        )
        result = XmlFormatter().format(directory)
        assert "<b>x & y</b>" in result
        assert "&lt;" not in result
        assert ET.fromstring(result).find("file").text.strip() == "<b>x & y</b>"

    def test_cdata_terminator_in_content_survives_round_trip(self):
        content = "a]]>b"
        directory = Directory(
            name="root",
            files=[File(name="x.txt", content=content, size=5)],
            subdirectories=[],
        )
        result = XmlFormatter().format(directory)
        assert ET.fromstring(result).find("file").text.strip() == content

    def test_special_chars_in_names_are_escaped(self):
        directory = Directory(
            name="root",
            files=[File(name='we"ird&<>.txt', content="x", size=1)],
            subdirectories=[],
        )
        root = ET.fromstring(XmlFormatter().format(directory))
        assert root.find("file").get("name") == 'we"ird&<>.txt'

    def test_indented_by_depth(self, nested_directory):
        result = XmlFormatter().format(nested_directory)
        assert '\n  <directory name="core">' in result
        assert '\n    <directory name="utils">' in result


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
