import pytest

from core.scanner import BaseScanner
from models import ScanConfig


@pytest.fixture
def scanner():
    return BaseScanner()


@pytest.fixture
def empty_config():
    return ScanConfig()


class TestBaseScanner:
    def test_scan_empty_dir(self, tmp_path, scanner, empty_config):
        result = scanner.scan(str(tmp_path), empty_config)

        assert result.directory.name == tmp_path.name
        assert result.directory.files == []
        assert result.directory.subdirectories == []

    def test_scan_with_files(self, tmp_path, scanner, empty_config):
        (tmp_path / "file.txt").write_text("content")
        (tmp_path / "file.py").write_text("print()")

        result = scanner.scan(str(tmp_path), empty_config)

        assert len(result.directory.files) == 2
        assert {f.name for f in result.directory.files} == {"file.txt", "file.py"}

    def test_scan_with_subdirectory(self, tmp_path, scanner, empty_config):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")

        result = scanner.scan(str(tmp_path), empty_config)

        assert len(result.directory.subdirectories) == 1
        assert result.directory.subdirectories[0].name == "subdir"
        assert result.directory.subdirectories[0].files[0].name == "nested.txt"

    def test_exclude_dirs(self, tmp_path, scanner):
        (tmp_path / ".git").mkdir()
        (tmp_path / "src").mkdir()
        config = ScanConfig(exclude_dirs=[".git"])

        result = scanner.scan(str(tmp_path), config)

        assert not any(d.name == ".git" for d in result.directory.subdirectories)
        assert any(d.name == "src" for d in result.directory.subdirectories)

    def test_exclude_files(self, tmp_path, scanner):
        (tmp_path / "main.py").write_text("code")
        (tmp_path / "data.pyc").write_bytes(b"\xff")
        config = ScanConfig(exclude_files=["*.pyc"])

        result = scanner.scan(str(tmp_path), config)

        assert not any(f.name == "data.pyc" for f in result.directory.files)
        assert any(f.name == "main.py" for f in result.directory.files)

    def test_exclude_content_dirs(self, tmp_path, scanner):
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "bundle.js").write_text("js")
        config = ScanConfig(exclude_content_dirs=["dist"])

        result = scanner.scan(str(tmp_path), config)

        dist_dir = next(d for d in result.directory.subdirectories if d.name == "dist")
        assert dist_dir.files == []
        assert dist_dir.subdirectories == []

    def test_exclude_content_files(self, tmp_path, scanner):
        (tmp_path / "app.log").write_text("logs")
        config = ScanConfig(exclude_content_files=["*.log"])

        result = scanner.scan(str(tmp_path), config)

        log_file = next(f for f in result.directory.files if f.name == "app.log")
        assert log_file.content == ""

    def test_permission_error(self, tmp_path, scanner, empty_config):
        locked = tmp_path / "locked"
        locked.mkdir()
        locked.chmod(0o000)

        result = scanner.scan(str(tmp_path), empty_config)

        locked_dir = next(d for d in result.directory.subdirectories if d.name == "locked")
        assert locked_dir.files == []
        locked.chmod(0o755)

    def test_max_depth_zero_hides_subdirectory_contents(self, tmp_path, scanner):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.txt").write_text("nested")
        (tmp_path / "root.txt").write_text("root")
        config = ScanConfig(max_depth=0)

        result = scanner.scan(str(tmp_path), config)

        assert any(f.name == "root.txt" for f in result.directory.files)
        sub_dir = next(d for d in result.directory.subdirectories if d.name == "sub")
        assert sub_dir.files == []
        assert sub_dir.subdirectories == []

    def test_max_depth_allows_recursion_up_to_limit(self, tmp_path, scanner):
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)
        (level1 / "a.txt").write_text("a")
        (level2 / "b.txt").write_text("b")
        config = ScanConfig(max_depth=1)

        result = scanner.scan(str(tmp_path), config)

        level1_dir = result.directory.subdirectories[0]
        assert any(f.name == "a.txt" for f in level1_dir.files)
        level2_dir = level1_dir.subdirectories[0]
        assert level2_dir.files == []
        assert level2_dir.subdirectories == []

    def test_max_file_size_replaces_content_with_placeholder(self, tmp_path, scanner):
        big = tmp_path / "big.bin"
        big.write_bytes(b"0" * 100)
        config = ScanConfig(max_file_size=10)

        result = scanner.scan(str(tmp_path), config)

        big_file = next(f for f in result.directory.files if f.name == "big.bin")
        assert big_file.content == "[File too large: 100 bytes]"
        assert big_file.size == 100

    def test_max_file_size_keeps_content_under_limit(self, tmp_path, scanner):
        small = tmp_path / "small.txt"
        small.write_text("hi")
        config = ScanConfig(max_file_size=10)

        result = scanner.scan(str(tmp_path), config)

        small_file = next(f for f in result.directory.files if f.name == "small.txt")
        assert small_file.content == "hi"

    def test_exclude_content_files_wins_over_max_file_size(self, tmp_path, scanner):
        big = tmp_path / "big.log"
        big.write_bytes(b"0" * 100)
        config = ScanConfig(max_file_size=10, exclude_content_files=["*.log"])

        result = scanner.scan(str(tmp_path), config)

        big_file = next(f for f in result.directory.files if f.name == "big.log")
        assert big_file.content == ""

    def test_include_files_keeps_only_matched(self, tmp_path, scanner):
        (tmp_path / "main.py").write_text("code")
        (tmp_path / "README.md").write_text("docs")
        config = ScanConfig(include_files=["*.py"])

        result = scanner.scan(str(tmp_path), config)

        assert {f.name for f in result.directory.files} == {"main.py"}

    def test_include_dirs_keeps_only_matched(self, tmp_path, scanner):
        (tmp_path / "src").mkdir()
        (tmp_path / "assets").mkdir()
        config = ScanConfig(include_dirs=["src"])

        result = scanner.scan(str(tmp_path), config)

        assert {d.name for d in result.directory.subdirectories} == {"src"}

    def test_empty_include_lists_keep_everything(self, tmp_path, scanner, empty_config):
        (tmp_path / "main.py").write_text("code")
        (tmp_path / "sub").mkdir()

        result = scanner.scan(str(tmp_path), empty_config)

        assert len(result.directory.files) == 1
        assert len(result.directory.subdirectories) == 1


class TestScanResult:
    def test_elapsed_is_positive(self, tmp_path, scanner, empty_config):
        result = scanner.scan(str(tmp_path), empty_config)

        assert result.elapsed > 0

    def test_file_count(self, tmp_path, scanner, empty_config):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")

        result = scanner.scan(str(tmp_path), empty_config)

        assert result.file_count == 2

    def test_dir_count(self, tmp_path, scanner, empty_config):
        (tmp_path / "sub1").mkdir()
        (tmp_path / "sub2").mkdir()

        result = scanner.scan(str(tmp_path), empty_config)

        assert result.dir_count == 2

    def test_nested_counts(self, tmp_path, scanner, empty_config):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.txt").write_text("x")
        (tmp_path / "root.txt").write_text("y")

        result = scanner.scan(str(tmp_path), empty_config)

        assert result.file_count == 2
        assert result.dir_count == 1