import pytest

from core.gitignore_manager import (
    _SECTION_HEADER,
    TREESNAKE_GITIGNORE_ENTRIES,
    GitignoreManager,
)


@pytest.fixture
def gitignore(tmp_path):
    return tmp_path / ".gitignore"


class TestGitignoreManager:
    def test_creates_gitignore_when_missing(self, gitignore):
        GitignoreManager(gitignore).update()

        assert gitignore.exists()

    def test_adds_all_entries_to_new_file(self, gitignore):
        GitignoreManager(gitignore).update()

        content = gitignore.read_text()
        for entry in TREESNAKE_GITIGNORE_ENTRIES:
            assert entry in content

    def test_ignores_cache_directory(self, gitignore):
        GitignoreManager(gitignore).update()

        assert ".treesnake/" in gitignore.read_text()

    def test_adds_section_header(self, gitignore):
        GitignoreManager(gitignore).update()

        assert _SECTION_HEADER in gitignore.read_text()

    def test_appends_to_existing_gitignore(self, gitignore):
        gitignore.write_text("node_modules\n.env\n", encoding="utf-8")

        GitignoreManager(gitignore).update()

        content = gitignore.read_text()
        assert "node_modules" in content
        assert ".env" in content
        for entry in TREESNAKE_GITIGNORE_ENTRIES:
            assert entry in content

    def test_does_not_duplicate_existing_entries(self, gitignore):
        existing = "\n".join(TREESNAKE_GITIGNORE_ENTRIES) + "\n"
        gitignore.write_text(existing, encoding="utf-8")

        GitignoreManager(gitignore).update()

        lines = [a.strip() for a in gitignore.read_text().splitlines()]
        for entry in TREESNAKE_GITIGNORE_ENTRIES:
            assert lines.count(entry) == 1

    def test_adds_only_missing_entries(self, gitignore):
        gitignore.write_text("treesnake\ntreesnake.exe\n", encoding="utf-8")

        GitignoreManager(gitignore).update()

        lines = [a.strip() for a in gitignore.read_text().splitlines()]
        assert lines.count("treesnake") == 1
        assert lines.count("treesnake.exe") == 1
        for entry in TREESNAKE_GITIGNORE_ENTRIES:
            assert entry in lines

    def test_separates_section_with_blank_line(self, gitignore):
        gitignore.write_text("node_modules\n", encoding="utf-8")

        GitignoreManager(gitignore).update()

        content = gitignore.read_text()
        header_index = content.index(_SECTION_HEADER)
        assert content[header_index - 1] == "\n"

    def test_no_extra_blank_line_for_empty_file(self, gitignore):
        gitignore.write_text("", encoding="utf-8")

        GitignoreManager(gitignore).update()

        assert not gitignore.read_text().startswith("\n")

    def test_no_changes_when_all_entries_present(self, gitignore):
        full_content = (
            _SECTION_HEADER + "\n" + "\n".join(TREESNAKE_GITIGNORE_ENTRIES) + "\n"
        )
        gitignore.write_text(full_content, encoding="utf-8")

        GitignoreManager(gitignore).update()

        assert gitignore.read_text() == full_content
