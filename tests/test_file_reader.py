from unittest.mock import patch
from core.file_reader import FileReader


class TestFileReader:
    def test_read_file(self, tmp_path):
        file = tmp_path / "test.txt"
        file.write_text("hello world", encoding="utf-8")

        result = FileReader().read(str(file))

        assert result.name == "test.txt"
        assert result.content == "hello world"
        assert result.size == file.stat().st_size

    def test_unreadable_file(self, tmp_path):
        file = tmp_path / "binary.bin"
        file.write_bytes(b"\xff\xfe")

        result = FileReader().read(str(file))

        assert result.content == FileReader.CONTENT_UNREADABLE

    def test_permission_error(self, tmp_path):
        file = tmp_path / "locked.txt"
        file.write_text("secret", encoding="utf-8")

        with patch("builtins.open", side_effect=PermissionError):
            result = FileReader().read(str(file))

        assert result.content == FileReader.CONTENT_UNREADABLE