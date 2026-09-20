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

    def test_binary_file_detected_by_nul_byte(self, tmp_path):
        file = tmp_path / "lib.dll"
        # валидный UTF-8, но с NUL — типичный бинарник
        file.write_bytes(b"MZ\x00\x00" + b"a" * 100)

        result = FileReader().read(str(file))

        assert result.content == FileReader.CONTENT_UNREADABLE

    def test_nul_beyond_sniff_window_still_unreadable(self, tmp_path):
        file = tmp_path / "late.bin"
        file.write_bytes(b"a" * (FileReader.BINARY_SNIFF_BYTES + 10) + b"\xff")

        result = FileReader().read(str(file))

        assert result.content == FileReader.CONTENT_UNREADABLE

    def test_crlf_normalized_like_text_mode(self, tmp_path):
        file = tmp_path / "win.txt"
        file.write_bytes(b"a\r\nb\rc\n")

        result = FileReader().read(str(file))

        assert result.content == "a\nb\nc\n"

    def test_uses_given_size_without_stat(self, tmp_path):
        file = tmp_path / "test.txt"
        file.write_text("hello", encoding="utf-8")

        with patch("os.path.getsize") as getsize:
            result = FileReader().read(str(file), size=42)

        getsize.assert_not_called()
        assert result.size == 42
        assert result.content == "hello"
